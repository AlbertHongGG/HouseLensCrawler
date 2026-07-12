from src.config import AppConfig
from src.spider.factory import SpiderFactory
from src.engine.manager import CrawlerManager

def main():
    print("Initializing HouseLens Crawler V2...")
    
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
