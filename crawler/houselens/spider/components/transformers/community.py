import re
from typing import Dict, Any, Optional
from houselens.models.community import StandardCommunity
from .base import BaseTransformer
from houselens.utils.parsers import parse_int, parse_float

class BaseCommunityTransformer(BaseTransformer):
    """
    Base class for transforming raw string dictionaries into a StandardCommunity.
    Provides default transformation functions for each field.
    Spider-specific transformers can inherit and override methods as needed.
    """
    
    def transform(self, raw_data: Dict[str, Any]) -> StandardCommunity:
        return StandardCommunity(
            community_uuid=self.transform_community_uuid(raw_data),
            source_platform=self.transform_source_platform(raw_data),
            source_id=self.transform_source_id(raw_data),
            url=self.transform_url(raw_data),
            name=self.transform_name(raw_data),
            address=self.transform_address(raw_data),
            builder=self.transform_builder(raw_data),
            contractor=self.transform_contractor(raw_data),
            completion_date=self.transform_completion_date(raw_data),
            age=self.transform_age(raw_data),
            total_households=self.transform_total_households(raw_data),
            building_structure=self.transform_building_structure(raw_data),
            land_zoning=self.transform_land_zoning(raw_data),
            image_url=self.transform_image_url(raw_data)
        )

    def transform_community_uuid(self, raw_data: Dict[str, Any]) -> str:
        plat = self.transform_source_platform(raw_data)
        sid = self.transform_source_id(raw_data)
        return f"{plat}_{sid}" if plat and sid else ""

    def transform_source_platform(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('source_platform', '')).strip()

    def transform_source_id(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('source_id', '')).strip()

    def transform_url(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('url', '')).strip()

    def transform_name(self, raw_data: Dict[str, Any]) -> str:
        return str(raw_data.get('name', '')).strip()

    def transform_address(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = raw_data.get('address')
        return str(val).strip() if val else None

    def transform_builder(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get('建設公司') or specs.get('投資建設') or specs.get('builder')
        return str(val).strip() if val else None

    def transform_contractor(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get('營造公司') or specs.get('contractor')
        return str(val).strip() if val else None

    def transform_completion_date(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get('完工日期') or specs.get('建築完成日') or specs.get('completion_date')
        return str(val).strip() if val else None

    def transform_age(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get('屋齡') or specs.get('age')
        return str(val).strip() if val else None

    def transform_total_households(self, raw_data: Dict[str, Any]) -> Optional[int]:
        specs = raw_data.get('specs', {})
        val = specs.get('總戶數') or specs.get('total_households')
        return parse_int(val)

    def transform_building_structure(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get('主結構') or specs.get('構造') or specs.get('建築構造') or specs.get('building_structure')
        return str(val).strip() if val else None

    def transform_land_zoning(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get('土地使用分區') or specs.get('土地分區') or specs.get('land_zoning')
        return str(val).strip() if val else None

    def transform_image_url(self, raw_data: Dict[str, Any]) -> Optional[str]:
        val = raw_data.get('image_url')
        return str(val).strip() if val else None
