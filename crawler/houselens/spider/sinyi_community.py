import logging
from typing import Optional
from DrissionPage import ChromiumPage

from .base import BaseSpider
from .factory import SpiderFactory
from ..models.community import StandardCommunity
from ..config import SpiderConfig

@SpiderFactory.register("sinyi_community")
class SinyiCommunitySpider(BaseSpider):
    def __init__(self, config: SpiderConfig, **kwargs):
        super().__init__(config, **kwargs)

    @property
    def platform_name(self) -> str:
        return "sinyi_community"

    def extract_source_id(self, url: str) -> Optional[str]:
        import re
        match = re.search(r'communityinfo/([A-Za-z0-9]+)', url)
        if match:
            return match.group(1)
        return None

    def start_requests(self, browser: ChromiumPage):
        url = "https://www.sinyi.com.tw/communitylist"
        self._load_page(browser, url)

    def process_detail_url(self, url: str, browser: ChromiumPage, context: dict) -> bool:
        logging.info(f"[sinyi_community] Processing community URL: {url}")
        
        detail_tab = browser.new_tab(url)
        try:
            # Wait for title to load
            detail_tab.wait.eles_loaded('tag:h1', timeout=10)
            
            raw_data = self.extract_raw_data(detail_tab)
            if not raw_data:
                return False
                
            community = self.transform(raw_data)
            
            from ..engine.events import event_bus, Event
            event_bus.emit(Event.COMMUNITY_PARSED, community=community)
                
            return True
        except Exception as e:
            logging.error(f"[sinyi_community] Error processing {url}: {e}")
            return False
        finally:
            detail_tab.close()

    def extract_raw_data(self, tab) -> Optional[dict]:
        try:
            # Get community title
            title_ele = tab.ele('tag:h1')
            name = title_ele.text.strip() if title_ele else ""
            
            # Get address
            address = ""
            addr_eles = tab.eles('@class:smallInfoCard_SmallInfoCard_Type_Address')
            if addr_eles:
                # Might be obfuscated, so we try a partial match
                pass
            if not address:
                # Find any div containing address-like text
                for div in tab.eles('tag:div'):
                    c = div.attr('class') or ""
                    if "Type_Address" in c:
                        address = div.text.strip()
                        break
            
            # Get specs from title/content pairs
            specs = {}
            titles = tab.eles('xpath://div[contains(@class, "community_basic-info-area-title")]')
            contents = tab.eles('xpath://div[contains(@class, "community_basic-info-area-content")]')
            
            for i in range(min(len(titles), len(contents))):
                label = titles[i].text.strip()
                value = contents[i].text.strip()
                specs[label] = value
                
            url = tab.url
            source_id = self.extract_source_id(url)
                
            if not source_id or not name:
                logging.error(f"[sinyi_community] Missing required fields (source_id: {source_id}, name: {name})")
                return None
                
            return {
                "source_id": source_id,
                "url": url,
                "name": name,
                "address": address,
                "specs": specs
            }
        except Exception as e:
            logging.error(f"[sinyi_community] Error extracting data: {e}")
            return None

    def transform(self, raw_data: dict) -> StandardCommunity:
        source_id = raw_data['source_id']
        community_uuid = f"sinyi_{source_id}"
        specs = raw_data.get('specs', {})
        
        total_households = None
        if "總戶數" in specs:
            import re
            match = re.search(r'\d+', specs["總戶數"])
            if match:
                total_households = int(match.group())
                
        builder = specs.get("建設公司") or specs.get("建商")
        completion_date = specs.get("屋齡")
        building_structure = specs.get("主結構") or specs.get("建築結構")
        
        return StandardCommunity(
            community_uuid=community_uuid,
            source_platform="sinyi",
            source_id=source_id,
            url=raw_data['url'],
            name=raw_data['name'],
            address=raw_data['address'],
            builder=builder,
            completion_date=completion_date,
            total_households=total_households,
            building_structure=building_structure,
            land_zoning=None
        )
