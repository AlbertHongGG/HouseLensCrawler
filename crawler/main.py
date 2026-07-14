import logging
from houselens.config import AppConfig
from houselens.spider.factory import SpiderFactory
from houselens.spider.components.strategies import FullCrawlStrategy, TargetedCrawlStrategy
from houselens.engine.manager import CrawlerEngine
from houselens.engine.events import event_bus
from houselens.extensions.storage_ext import StorageExtension
from houselens.storage.factory import StorageFactory
from houselens.extensions.visualizer_ext import VisualVerificationExtension
    
def main():
    logging.info("Initializing HouseLens Crawler V2...")
    
    # 0. Setup Event-Driven Architecture (Extensions)
    logging.info("Registering Extensions to EventBus...")
    
    # Storage Extension (always required)
    storage_strategy = StorageFactory.get_storage()
    StorageExtension(storage_strategy).setup(event_bus)
    
    # Visualizer Extension
    visualizer = VisualVerificationExtension()
    visualizer.setup(event_bus)
        
    # 1. Read Core Configuration
    max_workers = AppConfig.ENGINE_MAX_WORKERS
    
    # 2. Init Manager (Task Executor)
    manager = CrawlerEngine(max_workers=max_workers)
    
    # 3. Read Strategy configuration from .env
    crawl_mode = AppConfig.CRAWL_MODE
    logging.info(f"Crawl Mode: {crawl_mode.upper()}")
    
    tasks = []
    
    if crawl_mode == "targeted":
        target_platform = AppConfig.TARGET_PLATFORM
        target_urls = AppConfig.TARGET_URLS
        if not target_platform or not target_urls:
            logging.error("Target mode requires TARGET_PLATFORM and TARGET_URLS in .env")
            return
            
        try:
            spider = SpiderFactory.create(target_platform)
            strategy = TargetedCrawlStrategy(target_urls)
            tasks.append((spider, strategy))
        except ValueError as e:
            logging.error(f"Failed to create targeted spider: {e}")
            return
            
    else: # full mode
        active_platforms = AppConfig.ACTIVE_SPIDERS
        logging.info(f"Active platforms configured: {active_platforms}")
        
        for platform in active_platforms:
            try:
                spider = SpiderFactory.create(platform)
                strategy = FullCrawlStrategy()
                tasks.append((spider, strategy))
            except ValueError as e:
                logging.warning(f"{e}")

    if not tasks:
        logging.warning("No active tasks found. Exiting.")
        return

    # 4. Start engine with tasks
    manager.start(tasks)
    
    logging.info("Crawling finished.")

if __name__ == "__main__":
    main()
