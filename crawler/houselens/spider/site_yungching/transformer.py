import re
from typing import Dict, Any, Optional
from ..components.transformers.property import BasePropertyTransformer, parse_float
from houselens.models.property import StandardProperty
from ...utils.parsers import parse_layout, parse_floor

class YungchingTransformer(BasePropertyTransformer):
    """
    Yungching-specific property transformer.
    Overrides methods where Yungching strings need special cleaning.
    """
    def transform_source_platform(self, raw_data: Dict[str, Any]) -> str:
        return "yungching"

    def transform_property_uuid(self, raw_data: Dict[str, Any]) -> str:
        sid = self.transform_source_id(raw_data)
        return f"yc_{sid}" if sid else ""

    def transform_title(self, raw_data: Dict[str, Any]) -> str:
        title = super().transform_title(raw_data)
        sid = self.transform_source_id(raw_data)
        return title or f"永慶房屋 - {sid}"

    def transform_unit_price(self, raw_data: Dict[str, Any]) -> float:
        # Try unit_price first, fallback to unit_price_fallback
        up = parse_float(raw_data.get('unit_price'))
        if up <= 0:
            up = parse_float(raw_data.get('unit_price_fallback'))
        if up <= 0:
            tp = self.transform_total_price(raw_data)
            bp = self.transform_building_ping(raw_data)
            if tp > 0 and bp > 0:
                up = round(tp / bp, 2)
        return up

    def transform_address(self, raw_data: Dict[str, Any]) -> str:
        addr = str(raw_data.get('address', '')).strip()
        # "104台北市中山區南京東路三段\n看地圖" -> remove "看地圖"
        if '\n' in addr:
            addr = addr.split('\n')[0].strip()
        return addr

    def transform_rooms(self, raw_data: Dict[str, Any]) -> int:
        layout_text = str(raw_data.get('layout', ''))
        return parse_layout(layout_text).get('rooms', 0)

    def transform_living_rooms(self, raw_data: Dict[str, Any]) -> int:
        layout_text = str(raw_data.get('layout', ''))
        return parse_layout(layout_text).get('living_rooms', 0)

    def transform_bathrooms(self, raw_data: Dict[str, Any]) -> int:
        layout_text = str(raw_data.get('layout', ''))
        return parse_layout(layout_text).get('bathrooms', 0)

    def transform_floor(self, raw_data: Dict[str, Any]) -> str:
        floor_info = str(raw_data.get('floor_info', ''))
        f, _ = parse_floor(floor_info)
        return f

    def transform_total_floor(self, raw_data: Dict[str, Any]) -> str:
        floor_info = str(raw_data.get('floor_info', ''))
        _, tf = parse_floor(floor_info)
        return tf

    def transform_raw_building_type(self, raw_data: Dict[str, Any]) -> str:
        val = super().transform_raw_building_type(raw_data)
        if not val:
            layout_text = str(raw_data.get('layout', ''))
            if "型態" in layout_text:
                val = layout_text.split("型態")[-1].strip()
        return val

    def transform_community_name(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = super().transform_community_name(raw_data)
        if val and "看更多" in val:
            val = val.split("看更多")[0].strip()
        return val

    def transform_has_parking(self, raw_data: Dict[str, Any]) -> Optional[bool]:
        hp_text = str(raw_data.get('has_parking', ''))
        if hp_text:
            if "無車位" not in hp_text and "0個車位" not in hp_text and "0.0個車位" not in hp_text:
                return True
        return super().transform_has_parking(raw_data)

    def transform_management_fee(self, raw_data: Dict[str, Any]) -> Optional[str]:
        fee = super().transform_management_fee(raw_data)
        if fee:
            if "管理費" in fee:
                fee = fee.split("管理費")[-1].strip()
            elif "建物管理費" in fee:
                fee = fee.split("建物管理費")[-1].strip()
        return fee

    def transform_image_urls(self, raw_data: Dict[str, Any]) -> list:
        urls = super().transform_image_urls(raw_data)
        return [src for src in urls if src and "base64" not in src and "blank" not in src]
