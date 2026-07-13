import logging
import concurrent.futures
import signal
import sys
import time
from typing import List
from ..spider.base import BaseSpider
from ..config import AppConfig
from .browser_pool import browser_manager
from .context import EngineContext, SpiderContext

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class CrawlerEngine:
    """
    CrawlerEngine runs multiple Spiders concurrently.
    It manages the global EngineContext and handles Graceful Shutdown (Ctrl+C).
    """
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.context = EngineContext()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Register signal handlers for graceful shutdown on Ctrl+C."""
        def handle_sigint(signum, frame):
            logging.warning("\n[Engine] Ctrl+C received! Initiating graceful shutdown...")
            self.context.cancel()
            
            # 立即強制關閉所有活躍的瀏覽器，避免殭屍行程
            browser_manager.close_all()
            
            logging.warning("[Engine] Shutdown initiated. Waiting for threads to exit...")
            # 視需求，若不想等執行緒結束可以 sys.exit(0)，但正常來說交給 Executor shutdown() 就好
            
        signal.signal(signal.SIGINT, handle_sigint)
        signal.signal(signal.SIGTERM, handle_sigint)

    def _run_spider(self, spider: BaseSpider):
        """Worker thread entry point."""
        # 建立專屬的 SpiderContext
        spider_ctx = SpiderContext(self.context, max_items=spider.config.max_items)
        try:
            spider.run(spider_ctx)
        except Exception as e:
            logging.error(f"[{spider.platform_name}] Spider failed: {e}", exc_info=True)
        finally:
            if not AppConfig.BROWSER_REUSE_INSTANCE:
                logging.info(f"[{spider.platform_name}] Closing browser instance (BROWSER_REUSE_INSTANCE=False).")
                browser_manager.close_current_browser()

    def start(self, spiders: List[BaseSpider]):
        """
        Starts the execution of all provided spiders concurrently.
        """
        logging.info("Starting Crawler Engine...")
        
        # 不要用 with ... as executor，因為如果 Ctrl+C 觸發 KeyboardInterrupt，
        # with 區塊的 __exit__ 會呼叫 shutdown(wait=True)，這會卡死主執行緒。
        # 我們手動管理 executor，並在迴圈中監控狀態。
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        
        futures = []
        for spider in spiders:
            logging.info(f"[Engine] Submitting Spider: {spider.platform_name}")
            future = executor.submit(self._run_spider, spider)
            futures.append(future)

        try:
            # 使用迴圈與 timeout 來等待，這樣主執行緒就能夠隨時處理 Signal 與檢查狀態
            while not self.context.is_cancelled():
                done, not_done = concurrent.futures.wait(futures, timeout=1.0)
                
                # Check for exceptions in done futures
                for future in done:
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"[Engine] Future resulted in error: {e}")
                        
                if not not_done:
                    break # 所有任務皆已完成
        except KeyboardInterrupt:
            # 預防 Signal Handler 沒攔截到的例外狀況
            logging.warning("[Engine] KeyboardInterrupt caught! Shutting down...")
            self.context.cancel()
            browser_manager.close_all()
        finally:
            logging.info("[Engine] Cleaning up executor...")
            # 強制關閉 Executor，不等待已排隊但尚未執行的任務 (wait=False 不會 block 卡死)
            executor.shutdown(wait=False, cancel_futures=True)

        logging.info("Crawler engine finished all operations.")
