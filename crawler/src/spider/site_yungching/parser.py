import re
import logging
from typing import Dict, Any, Optional
from ...models.property import StandardProperty, BuildingType

from ..interfaces import IParser

class SpiderYungchingParser(IParser):
    """
    負責將 Yungching 網站抓取到的 DOM 元素字串，解析並清洗為 StandardProperty 格式。
    """
    def extract_source_id(self, url: str) -> str:
        # e.g. https://buy.yungching.com.tw/house/6763086
        return url.split('/')[-1].split('?')[0]
    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> StandardProperty:
        try:
            title = self._clean_text(elements.get('title'))
            if not title:
                title = f"永慶房屋 - {source_id}"
                
            total_price = self._parse_float(self._clean_text(elements.get('total_price')))
            address = self._clean_text(elements.get('address'))
            
            # 解析明細列
            layout_text = self._clean_text(elements.get('layout'))
            rooms, living_rooms, bathrooms = self._parse_layout(layout_text)
            
            building_ping = self._parse_ping(self._clean_text(elements.get('building_ping')), "建物坪數")
            main_ping = self._parse_ping(self._clean_text(elements.get('main_building_ping')), "主建物")
            shared_ping = self._parse_ping(self._clean_text(elements.get('shared_ping')), "共同使用小計")
            accessory_ping = self._parse_ping(self._clean_text(elements.get('accessory_ping')), "附屬建物小計")
            land_ping = self._parse_ping(self._clean_text(elements.get('land_ping')), "土地坪數")
            
            # 單價通常在房貸列
            unit_price = 0.0
            unit_price_text = self._clean_text(elements.get('unit_price'))
            # 尋找 "139.84萬/坪"
            match = re.search(r'([\d,.]+)\s*萬/坪', unit_price_text)
            if match:
                unit_price = self._parse_float(match.group(1))
                
            # 若單價為0，嘗試自行計算
            if unit_price == 0.0 and total_price > 0 and building_ping > 0:
                unit_price = round(total_price / building_ping, 2)
                
            age_text = self._clean_text(elements.get('age'))
            age = self._parse_age(age_text)
            floor_text = self._clean_text(elements.get('floor'))
            floor, total_floor = self._parse_floor(floor_text)
            
            raw_building_type = self._extract_after(layout_text, "型態")
            legal_usage = self._extract_after(self._clean_text(elements.get('legal_usage')), "謄本用途")
            land_zoning = self._extract_after(self._clean_text(elements.get('land_zoning')), "使用分區")
            
            community_name = self._extract_after(layout_text, "社區")
            if "更多社區資訊" in community_name:
                community_name = community_name.split("更多社區資訊")[0].strip()
                
            # Parking
            has_parking = False
            parking_type = ""
            has_parking_ele = elements.get('has_parking')
            if has_parking_ele:
                hp_text = self._clean_text(has_parking_ele)
                if "無車位" not in hp_text and "0個車位" not in hp_text and "0.0個車位" not in hp_text:
                    has_parking = True
                
            parking_text = self._clean_text(elements.get('parking_type'))
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
                    
            management_fee = self._clean_text(elements.get('management_fee'))
            if "管理費" in management_fee:
                management_fee = self._extract_after(management_fee, "管理費")
            elif "建物管理費" in management_fee:
                management_fee = self._extract_after(management_fee, "建物管理費")
                
            orientation = self._clean_text(elements.get('orientation'))
            if "朝向" in orientation:
                orientation = self._extract_after(orientation, "朝向")
                
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
                rooms=rooms,
                living_rooms=living_rooms,
                bathrooms=bathrooms,
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
            
    def _clean_text(self, ele: Optional[Any]) -> str:
        if not ele:
            return ""
        # 將多行文字合併為單行，方便處理
        return ele.text.replace('\n', ' ').strip()
        
    def _extract_after(self, text: str, keyword: str) -> str:
        """從字串中萃取某個關鍵字之後的數值"""
        if not text or keyword not in text:
            return ""
        # 簡單取 keyword 之後的下一個「單字」
        parts = text.split(keyword)
        if len(parts) > 1:
            val = parts[1].strip()
            return val.split(' ')[0] if ' ' in val else val
        return ""
        
    def _parse_float(self, text: str) -> float:
        if not text:
            return 0.0
        # 移除非數字和小數點的字元
        clean = re.sub(r'[^\d.]', '', text)
        try:
            return float(clean)
        except:
            return 0.0
            
    def _parse_ping(self, text: str, keyword: str = "") -> float:
        """從 '15.96坪' 中萃取 15.96，若指定 keyword，則從該 keyword 之後開始尋找"""
        if not text:
            return 0.0
            
        if keyword and keyword in text:
            parts = text.split(keyword, 1)
            if len(parts) > 1:
                text = parts[1]
                
        # 找到坪數數字
        match = re.search(r'([\d,.]+)\s*坪', text)
        if match:
            return self._parse_float(match.group(1))
        # 找不到坪，但有數字
        match = re.search(r'([\d,.]+)', text)
        if match:
             return self._parse_float(match.group(1))
        return 0.0
        
    def _parse_layout(self, text: str) -> tuple[int, int, int]:
        """從 '1房(室)2廳1衛' 中萃取 1, 2, 1"""
        rooms = living_rooms = bathrooms = 0
        if not text:
            return 0, 0, 0
            
        rm_match = re.search(r'(\d+)房', text)
        if rm_match: rooms = int(rm_match.group(1))
        
        lv_match = re.search(r'(\d+)廳', text)
        if lv_match: living_rooms = int(lv_match.group(1))
        
        bt_match = re.search(r'(\d+)衛', text)
        if bt_match: bathrooms = int(bt_match.group(1))
        
        return rooms, living_rooms, bathrooms
        
    def _parse_age(self, text: str) -> float:
        """從 '屋齡 13.8年' 萃取 13.8"""
        if not text:
            return 0.0
        match = re.search(r'屋齡\s*([\d.]+)\s*年', text)
        if match:
            return float(match.group(1))
        return 0.0
        
    def _parse_floor(self, text: str) -> tuple[str, str]:
        """從 '樓層 13~14/14樓' 萃取 '13~14' 和 '14F'"""
        if not text:
            return "", ""
        match = re.search(r'樓層\s*(.+?)\s*/\s*([\d~-]+)\s*樓?', text)
        if match:
            f = match.group(1).strip()
            tf = match.group(2).strip() + "F"
            return f, tf
        return "", ""
