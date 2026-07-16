import re
from typing import Dict, Any, Optional
from ..components.transformers.property import BasePropertyTransformer, parse_float
from houselens.models.property import StandardProperty

class Spider591Transformer(BasePropertyTransformer):
    def transform_source_platform(self, raw_data: Dict[str, Any]) -> str:
        return "591"

    def transform_property_uuid(self, raw_data: Dict[str, Any]) -> str:
        sid = self.transform_source_id(raw_data)
        # Note: we need to match the golden dataset uuid exactly without uuid4 random string
        # 591 golden dataset expects 591_{source_id}
        return f"591_{sid}" if sid else ""

    def transform_source_id(self, raw_data: Dict[str, Any]) -> str:
        url = raw_data.get('url', '')
        if url:
            match = re.search(r'detail/\d+/(\d+)\.html', url)
            if match:
                return match.group(1)
        return str(raw_data.get('source_id', ''))

    def transform_title(self, raw_data: Dict[str, Any]) -> str:
        title = super().transform_title(raw_data)
        if not title:
            sid = self.transform_source_id(raw_data)
            title = f"591物件 {sid}"
        return title

    def transform_parking_type(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('parking_info') or "").strip()
        if val and val != '無':
            return val
        return None

    def transform_has_parking(self, raw_data: Dict[str, Any]) -> Optional[bool]:
        val = str(raw_data.get('parking_info') or "").strip()
        if val and val != '無':
            return True
        elif val == '無':
            return False
        return super().transform_has_parking(raw_data)

    def transform_image_urls(self, raw_data: Dict[str, Any]) -> list:
        urls = super().transform_image_urls(raw_data)
        return [src for src in urls if src and "base64" not in src]

    def transform_has_tenant(self, raw_data: Dict[str, Any]) -> Optional[bool]:
        val = raw_data.get('has_tenant')
        if val is None:
            return None
        s_val = str(val).lower()
        if '是' in s_val:
            return True
        if '否' in s_val:
            return False
        return super().transform_has_tenant(raw_data)

    def transform_indoor_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        val = raw_data.get('indoor_ping')
        if val:
            parsed = parse_float(val)
            if parsed > 0:
                return parsed
        
        main = self.transform_main_building_ping(raw_data) or 0.0
        acc = self.transform_accessory_ping(raw_data) or 0.0
        if main > 0 or acc > 0:
            return round(main + acc, 2)
        return None
