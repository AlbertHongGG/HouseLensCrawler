import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from ..engine.events import event_bus, Event
from ..engine.context import SpiderContext
from ..engine.browser_pool import browser_manager
from .interfaces import INavigator, ITransformer
from .core.rules import MappingProfile, RuleEngine

class BaseSpider(ABC):
    """
    Base Spider class implementing the Template Method pattern.
    It orchestrates the crawling process using Navigator, RuleEngine, and Transformer components.
    """
    def __init__(self, config):
        self.config = config
        self.navigator: Optional[INavigator] = None
        self.profile: Optional[MappingProfile] = None
        self.transformer: Optional[ITransformer] = None
        
        # RuleEngine will automatically emit events if we pass a properly bound emitter
        self.rule_engine = RuleEngine(
            event_bus_emitter=lambda **kwargs: event_bus.emit(Event.ELEMENTS_LOCATED, **kwargs)
        )

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the name of the platform (e.g., '591', 'sinyi', 'yungching')"""
        pass

    def run(self, context: SpiderContext):
        """
        [Template Method] Executes the crawling pipeline.
        Subclasses MUST NOT override this method.
        """
        if not self.navigator or not self.profile or not self.transformer:
            logging.error(f"[{self.platform_name}] Spider components (Navigator, Profile, Transformer) are not properly initialized!")
            return

        logging.info(f"[{self.platform_name}] Spider starting...")
        event_bus.emit(Event.SPIDER_STARTED, platform_name=self.platform_name)

        # 1. 取得瀏覽器
        browser = browser_manager.get_browser()
        
        # 2. 取得起始網址
        start_url = self.config.start_url
        if not start_url:
            logging.error(f"[{self.platform_name}] start_url is empty! Please check .env file.")
            return

        page = 1
        items_processed = 0

        while page <= self.config.max_pages:
            # 檢查中斷或上限
            if context.is_cancelled():
                logging.warning(f"[{self.platform_name}] Spider cancelled. Stopping pagination.")
                break
            if context.reached_limit():
                logging.info(f"[{self.platform_name}] Global limit reached. Stopping.")
                break

            logging.info(f"[{self.platform_name}] Loading page {page}...")
            
            # 3. 進入列表頁
            if not self.navigator.load_list_page(browser, start_url, page):
                logging.info(f"[{self.platform_name}] No more list pages or failed to load. Stopping pagination.")
                break
                
            # 4. 提取當前頁面的所有物件網址
            urls_to_fetch = self.navigator.extract_item_urls(browser)
            logging.info(f"[{self.platform_name}] Found {len(urls_to_fetch)} items on page {page}.")

            if not urls_to_fetch:
                break

            # 5. 逐一處理每個網址
            for url in urls_to_fetch:
                if context.is_cancelled() or context.reached_limit():
                    break
                    
                # 6. 擷取 source_id 並去重
                source_id = self.transformer.extract_source_id(url)
                if not source_id:
                    continue

                if not context.add_and_check(source_id):
                    logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Duplicate or Limit Reached).")
                    continue
                
                logging.info(f"[{self.platform_name}] Opening tab for detail {source_id}...")
                detail_tab = None
                try:
                    # [開啟新分頁] 避免在同一個頁面反覆跳轉導致 JS 崩潰與記憶體洩漏
                    detail_tab = browser.new_tab(url)
                    
                    # [資料萃取] (Extractor/RuleEngine 層)
                    # 執行 MappingProfile，RuleEngine 會在內部自動發送 ELEMENTS_LOCATED 事件
                    raw_data = self.rule_engine.execute(
                        self.profile, 
                        detail_tab, 
                        source_id, 
                        self.platform_name
                    )
                    
                    # [資料轉換] (Transformer 層)
                    prop = self.transformer.transform(raw_data, url, source_id)
                    
                    if prop:
                        # 廣播事件：資料解析完畢 (供 Storage 存檔)
                        event_bus.emit(Event.ITEM_PARSED, item=prop)
                        items_processed += 1
                        logging.info(f"[{self.platform_name}] Parsed detail {source_id}.")
                    else:
                        logging.warning(f"[{self.platform_name}] Failed to transform {url}")
                        
                except Exception as e:
                    logging.error(f"[{self.platform_name}] Error processing {source_id}: {e}", exc_info=True)
                finally:
                    # [資源釋放] 確保分頁被關閉
                    if detail_tab:
                        detail_tab.close()
                        time.sleep(0.5)

            page += 1
            
        logging.info(f"[{self.platform_name}] Spider finished. Processed {items_processed} items.")
        event_bus.emit(Event.SPIDER_FINISHED, platform_name=self.platform_name)
