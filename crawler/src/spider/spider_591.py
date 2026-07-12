import time
import random
import uuid
import logging

from .base import BaseSpider
from ..models.property import StandardProperty
from .factory import SpiderFactory
from ..storage.factory import StorageFactory
from ..engine.state import global_state
from ..engine.browser_pool import browser_pool

@SpiderFactory.register("591")
class Spider591(BaseSpider):
    @property
    def platform_name(self) -> str:
        return "591"

    def run(self):
        """
        Executes the entire 591 crawling process sequentially.
        """
        logging.info(f"[{self.platform_name}] Spider starting...")
        
        # Instantiate required components directly
        storage = StorageFactory.get_storage()
        browser = browser_pool.get_browser()
        
        region_id = "1"
        page = 1
        
        while page <= self.config.max_pages:
            if global_state.reached_limit(self.config.max_items):
                logging.info(f"[{self.platform_name}] Global limit reached ({self.config.max_items}). Stopping.")
                break

            logging.info(f"[{self.platform_name}] Fetching list page {page} for region {region_id}...")
            time.sleep(0.5) # Mock list fetching
            
            # Mock finding 3 items on this page
            source_ids = [str(random.randint(1000000, 9999999)) for _ in range(3)]
            
            for source_id in source_ids:
                if global_state.reached_limit(self.config.max_items):
                    break
                    
                # Deduplication and counting
                if not global_state.add_and_check(source_id, self.config.max_items):
                    logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Duplicate).")
                    continue
                
                url = f"https://sale.591.com.tw/home/house/detail/2/{source_id}.html"
                logging.info(f"[{self.platform_name}] Fetching detail {source_id}...")
                
                # Mock detail fetching
                time.sleep(random.uniform(0.5, 1.5))
                
                prop = StandardProperty(
                    property_uuid=str(uuid.uuid4()),
                    source_platform="591",
                    source_id=source_id,
                    title=f"精選好屋 {source_id}",
                    total_price=random.randint(1000, 5000),
                    unit_price=random.uniform(30.0, 100.0),
                    building_ping=random.uniform(20.0, 60.0),
                    layout="3房2廳2衛",
                    age=random.uniform(0.0, 40.0),
                    floor="5F",
                    total_floor="15F",
                    address="台北市信義區信義路五段",
                    url=url
                )
                
                storage.save(prop)
                logging.info(f"[{self.platform_name}] Saved detail {source_id}.")

            page += 1
        
        logging.info(f"[{self.platform_name}] Spider finished.")
