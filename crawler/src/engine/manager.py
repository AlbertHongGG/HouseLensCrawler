import logging
import concurrent.futures
from typing import List
from ..spider.base import BaseSpider
from ..config import AppConfig
from .browser_pool import browser_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class CrawlerManager:
    """
    CrawlerManager runs multiple Spiders concurrently.
    Each Spider runs in its own thread and sequentially manages its internal tasks.
    """
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers

    def _run_spider(self, spider: BaseSpider):
        try:
            spider.run()
        finally:
            if not AppConfig.BROWSER_REUSE_INSTANCE:
                logging.info(f"[{spider.platform_name}] Closing browser instance (BROWSER_REUSE_INSTANCE=False).")
                browser_pool.close_current_browser()

    def start(self, spiders: List[BaseSpider]):
        """
        Starts the execution of all provided spiders concurrently.
        """
        logging.info("Starting crawler manager...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for spider in spiders:
                logging.info(f"[Manager] Submitting Spider: {spider.platform_name}")
                future = executor.submit(self._run_spider, spider)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"[Manager] Spider failed with error: {e}")

        logging.info("Crawler manager finished all spiders.")
