import logging
import time
from typing import Optional, List
from DrissionPage import ChromiumPage

from .interface import ICrawlStrategy
from ....config import CrawlMode
from ....storage.interfaces import IQueueStorage

class ConsumerStrategy(ICrawlStrategy):
    """
    Consumer Strategy reads target URLs from the crawl_queue using IQueueStorage
    and passes them to the spider's process_detail_url.
    """
    def __init__(self, queue_storage: IQueueStorage, **kwargs):
        self.queue_storage = queue_storage
        self.batch_size = kwargs.get("batch_size", 10)

    def execute(self, spider, browser: ChromiumPage, context: dict):
        logging.info(f"[{spider.platform_name}] Starting Consumer Strategy...")
        
        spider_name = spider.platform_name
        
        while True:
            # Fetch pending URLs from the queue
            try:
                # We want to process PENDING items for this specific spider
                # Also we should order by created_at or id to process older ones first
                pending_jobs = self.queue_storage.pop_pending_jobs(spider_name, self.batch_size)
                
                if not pending_jobs:
                    logging.info(f"[{spider_name}] No pending jobs found. Waiting...")
                    time.sleep(5)
                    break
                    
                for job in pending_jobs:
                    job_id = job['id']
                    url = job['url']
                    retry_count = job['retry_count']
                    
                    logging.info(f"[{spider_name}] Processing queued job {job_id}: {url}")
                    
                    try:
                        success = spider.process_detail_url(url, browser, context)
                        
                        if success:
                            self.queue_storage.update_job_status(job_id, "COMPLETED", retry_count)
                            logging.info(f"[{spider_name}] Job {job_id} completed successfully.")
                        else:
                            raise Exception("Spider returned False")
                    except Exception as e:
                        logging.error(f"[{spider_name}] Job {job_id} failed: {e}")
                        new_retry = retry_count + 1
                        new_status = "PENDING" if new_retry < 3 else "FAILED"
                        self.queue_storage.update_job_status(job_id, new_status, new_retry)
                        
            except Exception as e:
                logging.error(f"[{spider_name}] Error querying queue: {e}")
                time.sleep(5)
                break
