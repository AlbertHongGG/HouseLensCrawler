import logging
from houselens.config import AppConfig, CrawlMode
from houselens.spider.factory import SpiderFactory
from houselens.spider.components.strategies.factory import StrategyFactory
from houselens.engine.manager import CrawlerEngine
from houselens.engine.events import event_bus
from houselens.extensions.storage_ext import StorageExtension

from houselens.extensions.visualizer_ext import VisualVerificationExtension
from houselens.extensions.duplicate_logger_ext import DuplicateLoggerExtension
from houselens.storage.provider import StorageProvider
from houselens.extensions.queue_ext import CrawlQueueExtension
    
def main():
    logging.info("Initializing HouseLens Crawler V2...")
    
    # 0. Setup Event-Driven Architecture (Extensions)
    logging.info("Registering Extensions to EventBus...")
    
    # Get the unified storage instance
    storage = StorageProvider.get_storage()
    
    # Storage Extension (always required)
    StorageExtension(storage).setup(event_bus)
    
    # Visualizer Extension
    visualizer = VisualVerificationExtension()
    visualizer.setup(event_bus)
    
    # Duplicate Logger Extension
    DuplicateLoggerExtension()
    
    # Queue Extension (always required, will fallback to JSON Queue in local mode)
    CrawlQueueExtension(storage).setup(event_bus)
        
    # 1. Read Core Configuration
    max_workers = AppConfig.ENGINE_MAX_WORKERS
    
    # 2. Init Manager (Task Executor)
    manager = CrawlerEngine(max_workers=max_workers)
    
    # 3. Read Strategy configuration from .env
    crawl_mode = AppConfig.CRAWL_MODE
    logging.info(f"Crawl Mode: {crawl_mode.name}")
    
    tasks = []
    
    platforms_to_run = AppConfig.ACTIVE_SPIDERS
    if not platforms_to_run:
        logging.error("No active spiders configured in ACTIVE_SPIDERS.")
        return

    for platform in platforms_to_run:
        try:
            spider = SpiderFactory.create(platform)
            strategy = StrategyFactory.create(crawl_mode, config=spider.config)
            tasks.append((spider, strategy))
        except ValueError as e:
            logging.error(f"Failed to create spider or strategy for {platform}: {e}")

    if not tasks:
        logging.warning("No active tasks found. Exiting.")
        return

    # 4. Start engine with tasks
    manager.start(tasks)
    
    logging.info("Crawling finished.")

if __name__ == "__main__":
    main()
