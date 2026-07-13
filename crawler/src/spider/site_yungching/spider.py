import time
import logging
from typing import List, Dict, Any
from DrissionPage import ChromiumPage

from .locator import SpiderYungchingLocator
from .parser import SpiderYungchingParser
from ..base import BaseSpider
from ...config import SpiderConfig
from ...engine.events import event_bus, Event

class YungchingSpider(BaseSpider):
    """
    永慶房屋爬蟲實作。
    """
    
    def __init__(self, config: SpiderConfig):
        super().__init__(config)
        self.locator = SpiderYungchingLocator()
        self.parser = SpiderYungchingParser()

    @property
    def platform_name(self) -> str:
        return "yungching"

    def run(self, context):
        logging.info(f"[{self.platform_name}] Spider starting...")
        event_bus.emit(Event.SPIDER_STARTED, platform_name=self.platform_name)
        
        # 1. 取得瀏覽器
        from ...engine.browser_pool import browser_manager
        browser = browser_manager.get_browser()
        
        # 永慶房屋台北市全部列表
        base_url = self.config.start_url
        if not base_url:
            logging.error(f"[{self.platform_name}] start_url is empty! Please check .env file.")
            return
        page = 1
        items_processed = 0
        
        while page <= self.config.max_pages:
            if context.is_cancelled() or context.reached_limit():
                break
                
            list_url = f"{base_url}{page}"
            logging.info(f"[{self.platform_name}] Loading page: {list_url}")
            browser.get(list_url)
            time.sleep(3) # Wait for Angular
            
            items = self.locator.locate_list_items(browser)
            logging.info(f"[{self.platform_name}] Found {len(items)} items on page {page}.")
            
            if not items:
                break
                
            links: List[str] = []
            for item in items:
                a_tag = item.ele('tag:a', timeout=1)
                if a_tag:
                    links.append(a_tag.attr('href'))
                    
            if not links:
                break
                
            for link in links:
                if context.is_cancelled() or context.reached_limit():
                    break
                    
                # e.g. https://buy.yungching.com.tw/house/6763086
                source_id = link.split('/')[-1].split('?')[0]
                
                if not context.add_and_check(source_id):
                    continue
                
                try:
                    logging.info(f"[{self.platform_name}] Opening tab for detail {source_id}...")
                    detail_tab = browser.new_tab(link)
                    
                    elements = self.locator.locate_detail(detail_tab)
                    
                    event_bus.emit(
                        Event.ELEMENTS_LOCATED,
                        tab=detail_tab,
                        elements=elements,
                        source_id=f"yc_{source_id}",
                        platform_name=self.platform_name
                    )
                    
                    prop = self.parser.parse(elements, link, source_id)
                    
                    event_bus.emit(Event.ITEM_PARSED, item=prop)
                    
                    logging.info(f"[{self.platform_name}] Saved detail {source_id}.")
                    items_processed += 1
                    
                except Exception as e:
                    logging.error(f"[{self.platform_name}] Error processing {source_id}: {e}")
                finally:
                    if 'detail_tab' in locals():
                        detail_tab.close()
                        
            page += 1
            
        logging.info(f"[{self.platform_name}] Spider finished. Processed {items_processed} items.")
        event_bus.emit(Event.SPIDER_FINISHED, platform_name=self.platform_name)
