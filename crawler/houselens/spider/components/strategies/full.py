import logging
from typing import TYPE_CHECKING
from .interface import ICrawlStrategy

if TYPE_CHECKING:
    from ....base import BaseSpider
    from .....engine.context import SpiderContext

class FullCrawlStrategy(ICrawlStrategy):
    """
    完整爬取策略：負責從起始網址開始，逐頁翻頁並提取列表上的所有物件，並同步進行詳細頁爬取。
    """
    def execute(self, spider: 'BaseSpider', browser, context: 'SpiderContext') -> int:
        start_url = spider.config.start_url
        if not start_url:
            logging.error(f"[{spider.platform_name}] start_url is empty! Please check .env file.")
            return 0

        page = 1
        items_processed = 0

        while page <= spider.config.max_pages:
            if context.is_cancelled():
                logging.warning(f"[{spider.platform_name}] Spider cancelled. Stopping pagination.")
                break
            if context.reached_limit():
                logging.info(f"[{spider.platform_name}] Global limit reached. Stopping.")
                break

            logging.info(f"[{spider.platform_name}] Loading page {page}...")
            
            if not spider.navigator.load_list_page(browser, start_url, page):
                logging.info(f"[{spider.platform_name}] No more list pages or failed to load. Stopping pagination.")
                break
                
            urls_to_fetch = spider.navigator.extract_item_urls(browser)
            logging.info(f"[{spider.platform_name}] Found {len(urls_to_fetch)} items on page {page}.")

            if not urls_to_fetch:
                break

            for url in urls_to_fetch:
                if context.is_cancelled() or context.reached_limit():
                    break
                    
                if spider.process_detail_url(url, browser, context):
                    items_processed += 1

            page += 1
            
        return items_processed
