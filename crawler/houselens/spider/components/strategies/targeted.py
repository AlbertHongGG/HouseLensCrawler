import logging
from typing import List, TYPE_CHECKING
from .interface import ICrawlStrategy

if TYPE_CHECKING:
    from ....base import BaseSpider
    from .....engine.context import SpiderContext

class TargetedCrawlStrategy(ICrawlStrategy):
    """
    單點特定爬取策略：只針對傳入的特定網址清單進行爬取，略過翻頁邏輯。
    """
    def __init__(self, target_urls: List[str]):
        self.target_urls = target_urls
        
    def execute(self, spider: 'BaseSpider', browser, context: 'SpiderContext') -> int:
        logging.info(f"[{spider.platform_name}] Starting targeted crawl for {len(self.target_urls)} URLs...")
        items_processed = 0
        
        for url in self.target_urls:
            if context.is_cancelled() or context.reached_limit():
                break
            
            if spider.process_detail_url(url, browser, context):
                items_processed += 1
                
        return items_processed
