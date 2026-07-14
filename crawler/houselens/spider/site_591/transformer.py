import re
import uuid
from typing import Optional, Dict, Any
from ..components.transformers.interface import ITransformer
from ...models.property import StandardProperty
from ...utils.parsers import parse_layout, parse_floor

class Spider591Transformer(ITransformer):
    """
    負責解構 591 萃取出的純資料，轉換為 StandardProperty。
    不依賴任何瀏覽器物件，純函數實作。
    """
    
    def extract_source_id(self, url: str) -> str:
        match = re.search(r'detail/\d+/(\d+)\.html', url)
        return match.group(1) if match else ""

    def transform(self, raw_data: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        title = raw_data.get('title') or f"591物件 {source_id}"
        total_price = float(raw_data.get('total_price') or 0.0)
        unit_price = float(raw_data.get('unit_price') or 0.0)

        # 結構屬性
        layout_data = parse_layout(raw_data.get('layout'))
        age = float(raw_data.get('age') or 0.0)
        building_ping = float(raw_data.get('building_ping') or 0.0)
        
        floor, total_floor = parse_floor(raw_data.get('floor_info'))

        address = str(raw_data.get('address') or "").strip()
        community_name = str(raw_data.get('community_name') or "").strip()
        orientation = str(raw_data.get('orientation') or "").strip()

        raw_building_type = str(raw_data.get('raw_building_type') or "").strip()
        management_fee = str(raw_data.get('management_fee') or "").strip()
        
        has_tenant_str = str(raw_data.get('has_tenant') or "")
        has_tenant = True if '是' in has_tenant_str else False if '否' in has_tenant_str else None
        
        legal_usage = str(raw_data.get('legal_usage') or "").strip()
        
        # 車位處理
        parking_str = str(raw_data.get('parking_info') or "")
        has_parking = None
        parking_type = None
        if parking_str and parking_str != '無':
            has_parking = True
            parking_type = parking_str
        elif parking_str == '無':
            has_parking = False

        # 附屬建物
        main_building_ping = raw_data.get('main_building_ping')
        accessory_ping = raw_data.get('accessory_ping')
        shared_ping = raw_data.get('shared_ping')
        land_ping = raw_data.get('land_ping')

        prop = StandardProperty(
            property_uuid=f"591_{source_id}_{uuid.uuid4().hex[:8]}",
            source_platform="591",
            source_id=source_id,
            url=url,
            title=title,
            total_price=total_price,
            unit_price=unit_price,
            building_ping=building_ping,
            raw_building_type=raw_building_type or None,
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
            parking_type=parking_type or None,
            community_name=community_name or None,
            management_fee=management_fee or None,
            orientation=orientation or None,
            has_tenant=has_tenant,
            legal_usage=legal_usage or None,
            image_urls=[src for src in (raw_data.get('image_urls') or []) if src and "base64" not in src]
        )
        return prop
