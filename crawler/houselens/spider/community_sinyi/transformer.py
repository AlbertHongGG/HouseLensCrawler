import re
from typing import Dict, Any, Optional
from ...models.community import StandardCommunity

from ..components.transformers.community import BaseCommunityTransformer

class SinyiCommunityTransformer(BaseCommunityTransformer):
    """
    Transforms raw scraped data into a StandardCommunity model for Sinyi.
    """

    def transform_builder(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        builder = specs.get("建設公司") or specs.get("建商")
        if builder:
            builder = builder.strip()
        return builder if builder else None

    def transform_total_households(self, raw_data: Dict[str, Any]) -> Optional[int]:
        specs = raw_data.get('specs', {})
        val = specs.get("戶數") or specs.get("總戶數")
        from ...utils.parsers import parse_int
        return parse_int(val)
        
    def transform_building_structure(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        val = specs.get("主要結構") or specs.get("主結構") or specs.get("建築結構")
        return str(val).strip() if val else None
