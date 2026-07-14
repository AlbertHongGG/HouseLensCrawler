import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .components.strategies.interface import ICrawlStrategy

from ..engine.events import event_bus, Event
from ..engine.context import SpiderContext
from ..engine.browser_pool import browser_manager
from .components.navigators.interface import INavigator
from .components.transformers.interface import ITransformer
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

    def run(self, context: SpiderContext, strategy: 'ICrawlStrategy'):
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
        
        items_processed = 0
        try:
            items_processed = strategy.execute(self, browser, context)
        finally:
            logging.info(f"[{self.platform_name}] Spider finished. Processed {items_processed} items.")
            event_bus.emit(Event.SPIDER_FINISHED, platform_name=self.platform_name)

    def process_detail_url(self, url: str, browser, context: SpiderContext) -> bool:
        """
        處理單一物件網址，負責擷取、解析、與廣播事件。
        回傳是否成功處理該物件。
        """
        source_id = self.transformer.extract_source_id(url)
        if not source_id:
            return False

        if not context.add_and_check(source_id):
            logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Duplicate or Limit Reached).")
            return False
        
        logging.info(f"[{self.platform_name}] Opening tab for detail {source_id}...")
        detail_tab = None
        try:
            # [開啟新分頁] 避免在同一個頁面反覆跳轉導致 JS 崩潰與記憶體洩漏
            detail_tab = browser.new_tab(url)
            
            # [資料萃取] (Extractor/RuleEngine 層)
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
                logging.info(f"[{self.platform_name}] Parsed detail {source_id}.")
                return True
            else:
                logging.warning(f"[{self.platform_name}] Failed to transform {url}")
                return False
                
        except Exception as e:
            logging.error(f"[{self.platform_name}] Error processing {source_id}: {e}", exc_info=True)
            return False
        finally:
            # [資源釋放] 確保分頁被關閉
            if detail_tab:
                detail_tab.close()
                time.sleep(0.5)
