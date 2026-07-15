import re
from typing import Dict, Any, Optional
from ..components.transformers.base import BasePropertyTransformer, parse_float
from houselens.models.property import StandardProperty
from ...utils.parsers import parse_layout, parse_floor

class SinyiTransformer(BasePropertyTransformer):
    def transform_source_platform(self, raw_data: Dict[str, Any]) -> str:
        return "sinyi"

    def transform_property_uuid(self, raw_data: Dict[str, Any]) -> str:
        sid = self.transform_source_id(raw_data)
        return f"sinyi_{sid}" if sid else ""

    def transform_title(self, raw_data: Dict[str, Any]) -> str:
        title = super().transform_title(raw_data)
        if '｜' in title:
            title = title.split('｜')[0].strip()
        if not title:
            sid = self.transform_source_id(raw_data)
            title = f"信義房屋 - {sid}"
        return title

    def transform_address(self, raw_data: Dict[str, Any]) -> str:
        address = super().transform_address(raw_data).replace('地址', '')
        if '建坪' in address:
            address = address.split('建坪')[0]
        return address.strip()

    def transform_unit_price(self, raw_data: Dict[str, Any]) -> float:
        unit_price = super().transform_unit_price(raw_data)
        if not unit_price:
            total_price = self.transform_total_price(raw_data)
            building_ping = self.transform_building_ping(raw_data)
            if total_price > 0 and building_ping > 0:
                unit_price = round(total_price / building_ping, 2)
        return unit_price

    def transform_accessory_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        acc = super().transform_accessory_ping(raw_data)
        if not acc:
            balcony = parse_float(raw_data.get('balcony_ping'))
            rain = parse_float(raw_data.get('rain_cover_ping'))
            if balcony > 0 or rain > 0:
                acc = round(balcony + rain, 2)
        return acc

    def transform_indoor_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        # 1. 優先取 "主+附" (如果有被定位到 indoor_ping)
        indoor = parse_float(raw_data.get('indoor_ping'))
        if indoor > 0:
            return indoor
            
        # 2. 如果沒有 "主+附"，則必須：主建物存在，且 (陽台 or 雨遮 存在其一)，才進行計算
        main = parse_float(raw_data.get('main_building_ping'))
        balcony = parse_float(raw_data.get('balcony_ping'))
        rain = parse_float(raw_data.get('rain_cover_ping'))
        
        if main > 0 and (balcony > 0 or rain > 0):
            return round(main + balcony + rain, 2)
            
        return None

    def transform_raw_building_type(self, raw_data: Dict[str, Any]) -> Optional[str]:
        rb = super().transform_raw_building_type(raw_data)
        if rb:
            rb = rb.replace('--', '')
        return rb if rb else None

    def transform_floor(self, raw_data: Dict[str, Any]) -> str:
        floor_text = str(raw_data.get('floor_info') or "")
        f, _ = parse_floor(floor_text)
        return f.replace('樓', '').replace('B', '-').strip()

    def transform_total_floor(self, raw_data: Dict[str, Any]) -> str:
        floor_text = str(raw_data.get('floor_info') or "")
        _, tf = parse_floor(floor_text)
        return tf.replace('樓', '').strip()

    def transform_parking_type(self, raw_data: Dict[str, Any]) -> Optional[str]:
        pt = super().transform_parking_type(raw_data)
        if pt:
            pt = pt.replace('--', '').replace('無', '').strip()
        return pt if pt else None

    def transform_has_parking(self, raw_data: Dict[str, Any]) -> Optional[bool]:
        pt = self.transform_parking_type(raw_data)
        if pt:
            return True
        return False

    def transform_management_fee(self, raw_data: Dict[str, Any]) -> Optional[str]:
        mf = super().transform_management_fee(raw_data)
        if mf:
            mf = mf.replace('--', '')
        return mf if mf else None

    def transform_orientation(self, raw_data: Dict[str, Any]) -> Optional[str]:
        ort = super().transform_orientation(raw_data)
        if ort:
            ort = ort.replace('--', '')
        return ort if ort else None

    def transform_community_name(self, raw_data: Dict[str, Any]) -> Optional[str]:
        cn = super().transform_community_name(raw_data)
        if cn:
            cn = cn.replace('>', '').strip()
        return cn if cn else None

    def transform_image_urls(self, raw_data: Dict[str, Any]) -> list:
        urls = super().transform_image_urls(raw_data)
        return [src if src.startswith("http") else "https:" + src for src in urls if src]

    def transform_rooms(self, raw_data: Dict[str, Any]) -> int:
        layout_data = parse_layout(str(raw_data.get('layout') or ""))
        return layout_data.get('rooms', 0)

    def transform_living_rooms(self, raw_data: Dict[str, Any]) -> int:
        layout_data = parse_layout(str(raw_data.get('layout') or ""))
        return layout_data.get('living_rooms', 0)

    def transform_bathrooms(self, raw_data: Dict[str, Any]) -> int:
        layout_data = parse_layout(str(raw_data.get('layout') or ""))
        return layout_data.get('bathrooms', 0)
