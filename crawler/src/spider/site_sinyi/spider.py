import logging
import time
import re
from typing import List

from ..base import BaseSpider
from ..factory import SpiderFactory
from .locator import SinyiLocator
from .parser import SinyiParser
from ...models.property import StandardProperty
from ...engine.events import event_bus, Event

@SpiderFactory.register('sinyi')
class SinyiSpider(BaseSpider):
    @property
    def platform_name(self) -> str:
        return "sinyi"

    def __init__(self, config):
        super().__init__(config)
        self.locator = SinyiLocator()
        self.parser = SinyiParser()

    def run(self, context):
        logging.info(f"[{self.platform_name}] Spider starting...")
        
        # 1. 取得瀏覽器
        from ...engine.browser_pool import browser_manager
        browser = browser_manager.get_browser()
        
        # 信義房屋起始網址
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
            time.sleep(2) # 等待列表載入
            
            items = self.locator.locate_list_items(browser)
            logging.info(f"[{self.platform_name}] Found {len(items)} items on page {page}.")
            
            if not items:
                break
                
            links: List[str] = []
            for item in items:
                a_tag = item.ele('tag:a', timeout=1)
                if a_tag:
                    href = a_tag.attr('href')
                    if href:
                        links.append(href)
            
            # 開始逐筆爬取
            for link in links:
                if context.is_cancelled() or context.reached_limit():
                    break
                    
                match = re.search(r'/house/([A-Z0-9a-z]+)', link)
                if not match:
                    continue
                source_id = match.group(1)
                
                if not context.add_and_check(source_id):
                    logging.info(f"[{self.platform_name}] Detail {source_id} skipped.")
                    continue
                    
                try:
                    logging.info(f"[{self.platform_name}] Opening tab for detail {source_id}...")
                    detail_tab = browser.new_tab(link)
                    
                    elements = self.locator.locate_detail(detail_tab)
                    
                    # 廣播事件
                    event_bus.emit(
                        Event.ELEMENTS_LOCATED,
                        platform_name=self.platform_name,
                        source_id=source_id,
                        tab=detail_tab,
                        elements=elements
                    )
                    
                    prop = self.parser.parse(elements, link, source_id)
                    
                    if prop:
                        event_bus.emit(
                            Event.ITEM_PARSED,
                            item=prop
                        )
                        items_processed += 1
                        
                except Exception as e:
                    logging.error(f"[{self.platform_name}] Error parsing {link}: {e}", exc_info=True)
                finally:
                    if 'detail_tab' in locals() and detail_tab:
                        detail_tab.close()
            
            page += 1
            
        logging.info(f"[{self.platform_name}] Spider finished. Processed {items_processed} items.")
