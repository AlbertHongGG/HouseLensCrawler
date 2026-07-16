import re
from typing import Dict, Any, Optional
from ...models.community import StandardCommunity

from ..components.transformers.community import BaseCommunityTransformer

class Community591Transformer(BaseCommunityTransformer):
    """
    Transforms raw scraped data into a StandardCommunity model for 591.
    """

    def transform_builder(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        text = specs.get("builder", "")
        # 先找 value 在 label 前面的情況
        match = re.search(r'([^\s營造企劃]+)\s+(?:投資建設|建設公司)', text)
        if match:
            return match.group(1).strip()
        # 再找 label 在前面的情況
        match = re.search(r'(?:投資建設|建設公司)\s+([^\s營造企劃]+)', text)
        if match:
            return match.group(1).strip()
        return None

    def transform_contractor(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        text = specs.get("contractor", "")
        if not text:
            text = specs.get("builder", "") # 容錯：可能一起抓在 builder 區塊
        match = re.search(r'營造公司\s+([^建築企劃投資]+)', text)
        if match:
            return match.group(1).strip()
        return None
        
    def transform_building_structure(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        text = specs.get("building_structure", "")
        match = re.search(r'建築構造\s+([^車位棟戶座使公土地樓建]+)', text)
        if match:
            return match.group(1).strip()
        return None

    def transform_land_zoning(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        text = specs.get("land_zoning", "")
        match = re.search(r'土地分區\s+([^車位棟戶座使公建築樓建]+)', text)
        if match:
            return match.group(1).strip()
        return None
