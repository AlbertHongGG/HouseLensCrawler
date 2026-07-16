import re
from typing import Dict, Any, Optional
from houselens.models.property import StandardProperty
from .base import BaseTransformer
from ...utils.parsers import parse_float

class BasePropertyTransformer(BaseTransformer):
    """
    Base class for transforming raw string dictionaries into a StandardProperty.
    Provides default transformation functions for each field.
    Spider-specific transformers can inherit and override methods as needed.
    """
    
    def transform(self, raw_data: Dict[str, Any]) -> StandardProperty:
        url = raw_data.get('url', '')
        return StandardProperty(
            property_uuid=self.transform_property_uuid(raw_data),
            source_platform=self.transform_source_platform(raw_data),
            source_id=self.transform_source_id(raw_data),
            title=self.transform_title(raw_data),
            total_price=self.transform_total_price(raw_data),
            unit_price=self.transform_unit_price(raw_data),
            building_ping=self.transform_building_ping(raw_data),
            main_building_ping=self.transform_main_building_ping(raw_data),
            accessory_ping=self.transform_accessory_ping(raw_data),
            shared_ping=self.transform_shared_ping(raw_data),
            land_ping=self.transform_land_ping(raw_data),
            indoor_ping=self.transform_indoor_ping(raw_data),
            raw_building_type=self.transform_raw_building_type(raw_data),
            rooms=self.transform_rooms(raw_data),
            living_rooms=self.transform_living_rooms(raw_data),
            bathrooms=self.transform_bathrooms(raw_data),
            kitchens=self.transform_kitchens(raw_data),
            balconies=self.transform_balconies(raw_data),
            age=self.transform_age(raw_data),
            floor=self.transform_floor(raw_data),
            total_floor=self.transform_total_floor(raw_data),
            address=self.transform_address(raw_data),
            community_name=self.transform_community_name(raw_data),
            has_parking=self.transform_has_parking(raw_data),
            parking_type=self.transform_parking_type(raw_data),
            parking_ping=self.transform_parking_ping(raw_data),
            management_fee=self.transform_management_fee(raw_data),
            orientation=self.transform_orientation(raw_data),
            legal_usage=self.transform_legal_usage(raw_data),
            land_zoning=self.transform_land_zoning(raw_data),
            has_tenant=self.transform_has_tenant(raw_data),
            url=url,
            image_urls=self.transform_image_urls(raw_data)
        )

    def transform_land_zoning(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('land_zoning', '')).strip()
        return val if val and val != 'None' else None

    def transform_property_uuid(self, raw_data: Dict[str, Any]) -> str:
        plat = self.transform_source_platform(raw_data)
        sid = self.transform_source_id(raw_data)
        return f"{plat}_{sid}" if plat and sid else ""

    def transform_source_platform(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('source_platform', ''))

    def transform_source_id(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('source_id', ''))

    def transform_title(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('title', '')).strip()

    def transform_total_price(self, raw_data: Dict[str, Any]) -> float:
        return parse_float(raw_data.get('total_price')) or 0.0

    def transform_unit_price(self, raw_data: Dict[str, Any]) -> float:
        return parse_float(raw_data.get('unit_price')) or 0.0

    def transform_building_ping(self, raw_data: Dict[str, Any]) -> float:
        return parse_float(raw_data.get('building_ping')) or 0.0

    def transform_main_building_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        val = raw_data.get('main_building_ping')
        return parse_float(val) if val else None

    def transform_accessory_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        val = raw_data.get('accessory_ping')
        return parse_float(val) if val else None

    def transform_shared_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        val = raw_data.get('shared_ping')
        return parse_float(val) if val else None

    def transform_land_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        val = raw_data.get('land_ping')
        return parse_float(val) if val else None

    def transform_indoor_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        main = self.transform_main_building_ping(raw_data) or 0.0
        acc = self.transform_accessory_ping(raw_data) or 0.0
        if main > 0 or acc > 0:
            return main + acc
        return None

    def transform_raw_building_type(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('raw_building_type', '')).strip()
        return val if val else None

    def transform_rooms(self, raw_data: Dict[str, Any]) -> int:
        return int(parse_float(raw_data.get('rooms', 0)) or 0)

    def transform_living_rooms(self, raw_data: Dict[str, Any]) -> int:
        return int(parse_float(raw_data.get('living_rooms', 0)) or 0)

    def transform_bathrooms(self, raw_data: Dict[str, Any]) -> int:
        return int(parse_float(raw_data.get('bathrooms', 0)) or 0)

    def transform_kitchens(self, raw_data: Dict[str, Any]) -> int:
        return int(parse_float(raw_data.get('kitchens', 0)) or 0)

    def transform_balconies(self, raw_data: Dict[str, Any]) -> int:
        return int(parse_float(raw_data.get('balconies', 0)) or 0)

    def transform_age(self, raw_data: Dict[str, Any]) -> float:
        return parse_float(raw_data.get('age')) or 0.0

    def transform_floor(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('floor', '')).strip()

    def transform_total_floor(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('total_floor', '')).strip()

    def transform_address(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('address', '')).strip()

    def transform_community_name(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('community_name', '')).strip()
        return val if val else None

    def transform_has_parking(self, raw_data: Dict[str, Any]) -> Optional[bool]:
        val = raw_data.get('has_parking')
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        s_val = str(val).lower()
        if 'true' in s_val or '有' in s_val or '1' in s_val:
            return True
        if 'false' in s_val or '無' in s_val or '沒有' in s_val or '0' in s_val:
            return False
        return None

    def transform_parking_type(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('parking_type', '')).strip()
        return val if val else None

    def transform_parking_ping(self, raw_data: Dict[str, Any]) -> Optional[float]:
        val = raw_data.get('parking_ping')
        return parse_float(val) if val else None

    def transform_management_fee(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('management_fee', '')).strip()
        return val if val else None

    def transform_orientation(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('orientation', '')).strip()
        return val if val else None

    def transform_legal_usage(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = str(raw_data.get('legal_usage', '')).strip()
        return val if val else None

    def transform_has_tenant(self, raw_data: Dict[str, Any]) -> Optional[bool]:
        val = raw_data.get('has_tenant')
        if val is None:
            return None
        s_val = str(val).lower()
        if '是' in s_val or '有' in s_val or 'true' in s_val:
            return True
        if 'false' in s_val or '否' in s_val or '無' in s_val:
            return False
        return None

    def transform_image_urls(self, raw_data: Dict[str, Any]) -> list:
        val = raw_data.get('image_urls')
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            return [v.strip() for v in val.split(',') if v.strip()]
        return []
