import re
import logging
from typing import Dict, Any, Optional
from ...models.property import StandardProperty
from ..base_components import BaseParser

class SpiderYungchingParser(BaseParser):
    """
    負責將 Yungching 網站抓取到的 DOM 元素字串，解析並清洗為 StandardProperty 格式。
    """
    def extract_source_id(self, url: str) -> str:
        # e.g. https://buy.yungching.com.tw/house/6763086
        return url.split('/')[-1].split('?')[0]
        
    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> StandardProperty:
        try:
            title = self.clean_text(elements.get('title'))
            if not title:
                title = f"永慶房屋 - {source_id}"
                
            total_price = self.extract_float(self.clean_text(elements.get('total_price')))
            address = self.clean_text(elements.get('address'))
            
            # 解析明細列
            layout_text = self.clean_text(elements.get('layout'))
            layout_data = self.parse_layout(layout_text)
            
            building_ping = self.parse_ping(self.clean_text(elements.get('building_ping')), "建物坪數")
            main_ping = self.parse_ping(self.clean_text(elements.get('main_building_ping')), "主建物")
            shared_ping = self.parse_ping(self.clean_text(elements.get('shared_ping')), "共同使用小計")
            accessory_ping = self.parse_ping(self.clean_text(elements.get('accessory_ping')), "附屬建物小計")
            land_ping = self.parse_ping(self.clean_text(elements.get('land_ping')), "土地坪數")
            
            # 單價通常在房貸列
            unit_price = 0.0
            unit_price_text = self.clean_text(elements.get('unit_price'))
            match = re.search(r'([\d,.]+)\s*萬/坪', unit_price_text)
            if match:
                unit_price = self.extract_float(match.group(1))
                
            # 若單價為0，嘗試自行計算
            if unit_price == 0.0 and total_price > 0 and building_ping > 0:
                unit_price = round(total_price / building_ping, 2)
                
            age_text = self.clean_text(elements.get('age'))
            age = self.parse_age(age_text)
            floor_text = self.clean_text(elements.get('floor'))
            floor, total_floor = self.parse_floor(floor_text)
            
            raw_building_type = self.extract_after(layout_text, "型態")
            legal_usage = self.extract_after(self.clean_text(elements.get('legal_usage')), "謄本用途")
            land_zoning = self.extract_after(self.clean_text(elements.get('land_zoning')), "使用分區")
            
            community_name = self.extract_after(layout_text, "社區")
            if "更多社區資訊" in community_name:
                community_name = community_name.split("更多社區資訊")[0].strip()
                
            # Parking
            has_parking = False
            parking_type = ""
            has_parking_ele = elements.get('has_parking')
            if has_parking_ele:
                hp_text = self.clean_text(has_parking_ele)
                if "無車位" not in hp_text and "0個車位" not in hp_text and "0.0個車位" not in hp_text:
                    has_parking = True
                
            parking_text = self.clean_text(elements.get('parking_type'))
            if parking_text:
                if "坡道平面" in parking_text:
                    parking_type = "坡道平面"
                elif "機械" in parking_text:
                    parking_type = "機械"
                elif "坡道機械" in parking_text:
                    parking_type = "坡道機械"
                elif "塔式車位" in parking_text:
                    parking_type = "塔式車位"
                else:
                    parking_type = parking_text
                    
            management_fee = self.clean_text(elements.get('management_fee'))
            if "管理費" in management_fee:
                management_fee = self.extract_after(management_fee, "管理費")
            elif "建物管理費" in management_fee:
                management_fee = self.extract_after(management_fee, "建物管理費")
                
            orientation = self.clean_text(elements.get('orientation'))
            if "朝向" in orientation:
                orientation = self.extract_after(orientation, "朝向")
                
            prop = StandardProperty(
                property_uuid=f"yc_{source_id}",
                source_platform="yungching",
                source_id=source_id,
                title=title,
                total_price=total_price,
                unit_price=unit_price,
                builder=None,
                management_fee=management_fee or None,
                orientation=orientation or None,
                latitude=None,
                building_ping=building_ping,
                main_building_ping=main_ping,
                shared_ping=shared_ping,
                accessory_ping=accessory_ping,
                land_ping=land_ping,
                indoor_ping=round(main_ping + accessory_ping, 2) if main_ping else None,
                rooms=layout_data.get('rooms'),
                living_rooms=layout_data.get('living_rooms'),
                bathrooms=layout_data.get('bathrooms'),
                age=age,
                floor=floor,
                total_floor=total_floor,
                address=address,
                url=url,
                raw_building_type=raw_building_type,
                legal_usage=legal_usage,
                land_zoning=land_zoning,
                has_tenant=None,
                has_parking=has_parking,
                parking_type=parking_type or None,
                parking_ping=None,
                community_name=community_name
            )
            
            return prop
            
        except Exception as e:
            logging.error(f"[Parser] Failed to parse {url}: {e}")
            raise
