from src.config import AppConfig
from src.spider.factory import SpiderFactory
from src.engine.manager import CrawlerManager
from src.engine.events import event_bus
from src.extensions.storage_ext import StorageExtension
from src.storage.factory import StorageFactory
from src.extensions.visualizer_ext import VisualVerificationExtension
    
def main():
    print("Initializing HouseLens Crawler V2...")
    
    # 0. Setup Event-Driven Architecture (Extensions)
    print("Registering Extensions to EventBus...")
    
    # Storage Extension (always required)
    storage_strategy = StorageFactory.get_storage()
    StorageExtension(storage_strategy).setup(event_bus)
    
    # Visualizer Extension (optional)
    if AppConfig.ENABLE_VISUAL_VERIFICATION:
        print("Visual Verification Extension Enabled.")
        VisualVerificationExtension(output_dir="data").setup(event_bus)
        
    # 1. Read Core Configuration
    max_workers = AppConfig.ENGINE_MAX_WORKERS
    
    # 2. Init Manager (Task Executor)
    manager = CrawlerManager(max_workers=max_workers)
    
    # 3. Load active spiders from .env
    active_platforms = AppConfig.ACTIVE_SPIDERS
    print(f"Active platforms configured: {active_platforms}")
    print(f"Engine max workers: {max_workers}")
    
    spiders = []
    for platform in active_platforms:
        try:
            spider = SpiderFactory.create(platform)
            spiders.append(spider)
        except ValueError as e:
            print(f"Warning: {e}")

    if not spiders:
        print("No active spiders found. Exiting.")
        return

    # 4. Start engine with spiders
    manager.start(spiders)
    
    print("Crawling finished.")

if __name__ == "__main__":
    main()
