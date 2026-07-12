import re
import uuid
from typing import Optional, Dict, Any
from ...models.property import StandardProperty

class Spider591Parser:
    """
    負責解構 591 元素字典的解析器 (Parser 層)。
    符合單一職責原則：不依賴任何 DOM 導航邏輯與瀏覽器物件，純粹將傳入的 Element 萃取出純文字，並進行清洗與轉型。
    """
    
    def __init__(self, platform_name: str = "591"):
        self.platform_name = platform_name

    def _extract_float(self, text: str) -> Optional[float]:
        """
        [工具] 從字串中萃取浮點數，去除逗號與雜訊。
        例如 "1,200.5萬" -> 1200.5
        """
        if not text:
            return None
        match = re.search(r'[\d\.]+', text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def _clean_text(self, ele: Optional[Any], label: str = "") -> str:
        """
        [工具] 從傳入的元素提取純文字，並剔除標籤與冒號雜訊。
        """
        if not ele:
            return ""
            
        raw_text = ele.text
        if label:
            val = raw_text.replace(label, '').replace('：', '').replace(':', '').strip()
        else:
            val = raw_text.strip()
            
        # 避免抓到外層大區塊導致字串過長
        if len(val) < 100:
            return val
        return ""

    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> StandardProperty:
        """
        [解析核心] 接收 Locator 整理好的元素字典，提取資訊並對應到 StandardProperty。
        """
        # [1] 基本屬性：標題、總價、單價
        title = self._clean_text(elements.get('title')) or f"591物件 {source_id}"
        total_price = self._extract_float(self._clean_text(elements.get('total_price'))) or 0.0
        unit_price = self._extract_float(self._clean_text(elements.get('unit_price'))) or 0.0

        # [2] 結構屬性：格局、屋齡、權狀坪數、樓層
        layout = self._clean_text(elements.get('layout'), '格局')
        age = self._extract_float(self._clean_text(elements.get('age'), '屋齡')) or 0.0
        building_ping = self._extract_float(self._clean_text(elements.get('building_ping'), '權狀坪數')) or 0.0
        
        floor = ""
        total_floor = ""
        floor_text = self._clean_text(elements.get('floor_info'), '樓層')
        if '/' in floor_text:
            floor, total_floor = floor_text.split('/', 1)
        else:
            floor = floor_text

        # [3] 地理與社群：地址、社區名稱
        address = self._clean_text(elements.get('address'), '地址')
        community_name = self._clean_text(elements.get('community_name'), '社區')

        # [4] 詳細資訊區塊：型態、車位、坪數細節
        raw_building_type = self._clean_text(elements.get('raw_building_type'), '型態')
        management_fee = self._clean_text(elements.get('management_fee'), '管理費')
        
        has_tenant_str = self._clean_text(elements.get('has_tenant'), '帶租約')
        has_tenant = "是" in has_tenant_str if has_tenant_str else None
        
        legal_usage = self._clean_text(elements.get('legal_usage'), '法定用途')
        
        parking_str = self._clean_text(elements.get('parking_info'), '車位')
        has_parking = "無" not in parking_str if parking_str else None
        parking_ping = self._extract_float(parking_str) if has_parking else None

        main_ping = self._extract_float(self._clean_text(elements.get('main_building_ping'), '主建物'))
        accessory_ping = self._extract_float(self._clean_text(elements.get('accessory_ping'), '附屬建物'))
        shared_ping = self._extract_float(self._clean_text(elements.get('shared_ping'), '共用部分'))
        land_ping = self._extract_float(self._clean_text(elements.get('land_ping'), '土地坪數'))

        # [5] 組裝與映射：產生標準物件
        return StandardProperty(
            property_uuid=str(uuid.uuid4()),
            source_platform=self.platform_name,
            source_id=source_id,
            title=title,
            total_price=total_price,
            unit_price=unit_price,
            building_ping=building_ping,
            layout=layout,
            age=age,
            floor=floor.strip(),
            total_floor=total_floor.strip(),
            address=address,
            url=url,
            raw_building_type=raw_building_type,
            main_building_ping=main_ping,
            accessory_ping=accessory_ping,
            shared_ping=shared_ping,
            land_ping=land_ping,
            has_parking=has_parking,
            parking_type=parking_str,
            parking_ping=parking_ping,
            legal_usage=legal_usage,
            has_tenant=has_tenant,
            community_name=community_name,
            management_fee=management_fee
        )
