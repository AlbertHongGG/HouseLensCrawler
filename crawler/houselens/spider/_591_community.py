import logging
from typing import Optional
from DrissionPage import ChromiumPage

from .base import BaseSpider
from .factory import SpiderFactory
from ..models.community import StandardCommunity
from ..config import SpiderConfig

@SpiderFactory.register("591_community")
class _591CommunitySpider(BaseSpider):
    def __init__(self, config: SpiderConfig, **kwargs):
        super().__init__(config, **kwargs)

    @property
    def platform_name(self) -> str:
        return "591_community"
        
    def extract_source_id(self, url: str) -> Optional[str]:
        import re
        match = re.search(r'market\.591\.com\.tw/(\d+)', url)
        if match:
            return match.group(1)
        return None
        
    def start_requests(self, browser: ChromiumPage):
        # The community spider runs primarily via the crawl queue,
        # but if we wanted to crawl all communities from scratch:
        url = "https://market.591.com.tw/list"
        self._load_page(browser, url)
        # We don't implement full pagination for community list right now,
        # we focus on targeted crawling from queue.
        
    def process_detail_url(self, url: str, browser: ChromiumPage, context: dict) -> bool:
        """
        Process a single community detail page.
        """
        logging.info(f"[591_community] Processing community URL: {url}")
        
        detail_tab = browser.new_tab(url)
        try:
            # Wait for main info container
            detail_tab.wait.eles_loaded('tag:h1', timeout=10)
            
            raw_data = self.extract_raw_data(detail_tab)
            if not raw_data:
                return False
                
            community = self.transform(raw_data)
            
            # Save using event bus
            from ..engine.events import event_bus, Event
            event_bus.emit(Event.COMMUNITY_PARSED, community=community)
                
            return True
        except Exception as e:
            logging.error(f"[591_community] Error processing {url}: {e}")
            return False
        finally:
            detail_tab.close()

    def extract_raw_data(self, tab) -> Optional[dict]:
        """
        Extract raw community data from 591 community detail page.
        """
        try:
            # Get community title
            title_ele = tab.ele('tag:h1')
            name = title_ele.text.strip() if title_ele else ""
            
            # Get address
            address = ""
            
            # Basic specs
            specs = {}
            spec_items = tab.eles('.info-item')
            for item in spec_items:
                text = item.text.strip().replace('\n', ' ')
                if "地址" in text:
                    address = text.replace("地址", "").strip()
                elif "屋齡" in text:
                    specs["屋齡"] = text.replace("屋齡", "").strip()
                elif "總戶數" in text:
                    specs["總戶數"] = text.replace("總戶數", "").strip()
                elif "建築型態" in text:
                    specs["建築型態"] = text.replace("建築型態", "").strip()
                # other fields can be extracted if needed...
                    
            # Parse URL to get source_id
            url = tab.url
            source_id = self.extract_source_id(url)
                
            if not source_id or not name:
                logging.error(f"[591_community] Missing required fields (source_id: {source_id}, name: {name})")
                return None
                
            return {
                "source_id": source_id,
                "url": url,
                "name": name,
                "address": address,
                "specs": specs
            }
        except Exception as e:
            logging.error(f"[591_community] Error extracting data: {e}")
            return None

    def transform(self, raw_data: dict) -> StandardCommunity:
        """
        Transform raw data into StandardCommunity.
        """
        source_id = raw_data['source_id']
        community_uuid = f"591_{source_id}"
        
        specs = raw_data.get('specs', {})
        
        total_households = None
        if "總戶數" in specs:
            import re
            match = re.search(r'\d+', specs["總戶數"])
            if match:
                total_households = int(match.group())
                
        # Some 591 fields might be mapped differently depending on exact DOM
        builder = specs.get("建設公司")
        completion_date = specs.get("建築完成日") or specs.get("屋齡")
        building_structure = specs.get("建築結構")
        land_zoning = specs.get("土地使用分區")
        
        return StandardCommunity(
            community_uuid=community_uuid,
            source_platform="591",
            source_id=source_id,
            url=raw_data['url'],
            name=raw_data['name'],
            address=raw_data['address'],
            builder=builder,
            completion_date=completion_date,
            total_households=total_households,
            building_structure=building_structure,
            land_zoning=land_zoning
        )
