import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from .components.strategies.interface import ICrawlStrategy

from ..engine.events import event_bus, Event
from ..engine.context import SpiderContext
from ..engine.browser import browser_manager
from ..engine.dedup import CheckStatus
from .components.navigators.base import BaseNavigator
from .components.transformers.base import BasePropertyTransformer

class BaseSpider(ABC):
    """
    Base Spider class.
    Orchestrates extraction using Naked DrissionPage locators and delegates
    transformation to BasePropertyTransformer.
    """
    def __init__(self, config):
        self.config = config
        self.navigator: Optional[BaseNavigator] = None
        self.transformer: Optional[BasePropertyTransformer] = None
        self.raw_elements: Dict[str, Any] = {}

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the name of the platform (e.g., '591', 'sinyi', 'yungching')"""
        pass

    @abstractmethod
    def extract_source_id(self, url: str) -> Optional[str]:
        """Extracts the unique source ID from the URL."""
        pass

    @abstractmethod
    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        [Template Method for Implementors]
        Extract raw strings from the webpage using DrissionPage.
        Should define block containers and query elements inside those containers.
        Returns a dictionary of raw strings mapping to StandardProperty fields.
        Implementors should optionally store elements in `self.raw_elements` for visualization.
        """
        pass

    def process_detail_url(self, url: str, browser: Any, context: SpiderContext, force_scrape: bool = False) -> bool:
        """
        處理單一物件網址，負責擷取、解析、與廣播事件。
        回傳是否成功處理該物件。
        """
        if not self.transformer:
            logging.error(f"[{self.platform_name}] Transformer is not initialized!")
            return False

        source_id = self.extract_source_id(url)
        if not source_id:
            return False

        status, original_url = context.register_item(source_id, url)
        if status == CheckStatus.LIMIT_REACHED:
            logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Limit Reached).")
            return False
        elif status == CheckStatus.DUPLICATE:
            if not force_scrape:
                logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Duplicate).")
                event_bus.emit(Event.DUPLICATE_DETECTED, platform=self.platform_name, source_id=source_id, url_a=original_url, url_b=url)
                return False
            else:
                logging.info(f"[{self.platform_name}] Detail {source_id} is a duplicate, but force_scrape is True. Proceeding.")
        
        logging.info(f"[{self.platform_name}] Opening tab for detail {source_id}...")
        detail_tab = None
        try:
            # [開啟新分頁]
            detail_tab = browser.new_tab(url)
            
            # [前置處理]
            if self.navigator and hasattr(self.navigator, 'prepare_detail_page'):
                self.navigator.prepare_detail_page(detail_tab)
            
            # [原物料擷取]
            self.raw_elements.clear()
            raw_data = self.extract_raw_data(detail_tab, url)
            
            # [視覺化截圖]
            if self.raw_elements:
                event_bus.emit(Event.ELEMENTS_LOCATED, tab=detail_tab, elements=self.raw_elements, source_id=source_id, platform_name=self.platform_name)

            # 補上必要的 ID 欄位
            raw_data['source_platform'] = self.platform_name
            raw_data['source_id'] = source_id
            raw_data['url'] = url
            
            # [資料清洗與轉換]
            prop = self.transformer.transform(raw_data, url)
            
            if prop:
                # 廣播事件：資料解析完畢
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
            if detail_tab:
                detail_tab.close()
                time.sleep(0.5)
