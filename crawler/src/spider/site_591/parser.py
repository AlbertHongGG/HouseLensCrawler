import re
import uuid
from typing import Optional, Dict, Any
from ...models.property import StandardProperty
from ..base_components import BaseParser

class Spider591Parser(BaseParser):
    """
    負責解構 591 元素字典的解析器 (Parser 層)。
    符合單一職責原則：不依賴任何 DOM 導航邏輯與瀏覽器物件，純粹將傳入的 Element 萃取出純文字，並進行清洗與轉型。
    """
    
    def extract_source_id(self, url: str) -> str:
        """從 URL 擷取 591 的 source_id"""
        match = re.search(r'detail/\d+/(\d+)\.html', url)
        return match.group(1) if match else ""

    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> StandardProperty:
        """
        [解析核心] 接收 Locator 整理好的元素字典，提取資訊並對應到 StandardProperty。
        """
        # [1] 基本屬性：標題、總價、單價
        title = self.clean_text(elements.get('title')) or f"591物件 {source_id}"
        total_price = self.extract_float(self.clean_text(elements.get('total_price'))) or 0.0
        unit_price = self.extract_float(self.clean_text(elements.get('unit_price'))) or 0.0

        # [2] 結構屬性：格局、屋齡、權狀坪數、樓層
        layout_str = self.clean_text(elements.get('layout'), '格局')
        layout_data = self.parse_layout(layout_str)
        
        age = self.parse_age(self.clean_text(elements.get('age'), '屋齡')) or 0.0
        building_ping = self.extract_float(self.clean_text(elements.get('building_ping'), '權狀坪數')) or 0.0
        
        floor_text = self.clean_text(elements.get('floor_info'), '樓層')
        floor, total_floor = self.parse_floor(floor_text)

        # [3] 地理與社群：地址、社區名稱
        address = self.clean_text(elements.get('address'), '地址')
        community_name = self.clean_text(elements.get('community_name'), '社區')
        orientation = self.clean_text(elements.get('orientation'), '朝向')

        # [4] 詳細資訊區塊：型態、車位、坪數細節
        raw_building_type = self.clean_text(elements.get('raw_building_type'), '型態')
        management_fee = self.clean_text(elements.get('management_fee'), '管理費')
        
        has_tenant_str = self.clean_text(elements.get('has_tenant'), '帶租約')
        has_tenant = True if '是' in has_tenant_str else False if '否' in has_tenant_str else None
        
        legal_usage = self.clean_text(elements.get('legal_usage'), '法定用途')
        
        # 處理車位：有時候 591 把車位寫在 "車位" 欄，有時則是分開
        parking_str = self.clean_text(elements.get('parking_info'), '車位')
        has_parking = None
        parking_type = None
        if parking_str and parking_str != '無':
            has_parking = True
            parking_type = parking_str
        elif parking_str == '無':
            has_parking = False

        # [5] 附屬建物與主建物
        main_building_ping = self.extract_float(self.clean_text(elements.get('main_building_ping'), '主建物')) or None
        accessory_ping = self.extract_float(self.clean_text(elements.get('accessory_ping'), '附屬建物')) or None
        shared_ping = self.extract_float(self.clean_text(elements.get('shared_ping'), '公設')) or None
        land_ping = self.extract_float(self.clean_text(elements.get('land_ping'), '土地坪數')) or None

        # [6] 建立 StandardProperty 物件
        prop = StandardProperty(
            property_uuid=f"591_{source_id}_{uuid.uuid4().hex[:8]}",
            source_platform="591",
            source_id=source_id,
            url=url,
            title=title,
            total_price=total_price,
            unit_price=unit_price,
            building_ping=building_ping,
            raw_building_type=raw_building_type,
            rooms=layout_data.get('rooms'),
            living_rooms=layout_data.get('living_rooms'),
            bathrooms=layout_data.get('bathrooms'),
            kitchens=layout_data.get('kitchens'),
            balconies=layout_data.get('balconies'),
            age=age,
            floor=floor,
            total_floor=total_floor,
            address=address,
            main_building_ping=main_building_ping,
            accessory_ping=accessory_ping,
            shared_ping=shared_ping,
            land_ping=land_ping,
            has_parking=has_parking,
            parking_type=parking_type,
            community_name=community_name,
            management_fee=management_fee,
            orientation=orientation,
            has_tenant=has_tenant,
            legal_usage=legal_usage
        )
        return prop
