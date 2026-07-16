import re
from typing import Dict, Any, Optional
from ...models.community import StandardCommunity


class Community591Transformer:
    """
    Transforms raw scraped data into a StandardCommunity model for 591.
    """

    def transform(self, raw_data: Dict[str, Any]) -> StandardCommunity:
        source_id = raw_data['source_id']
        specs = raw_data.get('specs', {})

        return StandardCommunity(
            community_uuid=f"591_{source_id}",
            source_platform="591",
            source_id=source_id,
            url=raw_data['url'],
            name=raw_data['name'],
            address=raw_data.get('address'),
            builder=self._extract_builder(specs),
            contractor=self._extract_contractor(specs),
            completion_date=specs.get("建築完成日"),
            age=specs.get("屋齡"),
            total_households=self._parse_households(specs.get("總戶數")),
            building_structure=self._extract_building_structure(specs),
            land_zoning=self._extract_land_zoning(specs),
            image_url=raw_data.get('image_url')
        )

    def _extract_builder(self, specs: Dict[str, str]) -> Optional[str]:
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

    def _extract_contractor(self, specs: Dict[str, str]) -> Optional[str]:
        text = specs.get("contractor", "")
        if not text:
            text = specs.get("builder", "") # 容錯：可能一起抓在 builder 區塊
        match = re.search(r'營造公司\s+([^建築企劃投資]+)', text)
        if match:
            return match.group(1).strip()
        return None
        
    def _extract_building_structure(self, specs: Dict[str, str]) -> Optional[str]:
        text = specs.get("building_structure", "")
        match = re.search(r'建築構造\s+([^車位棟戶座使公土地樓建]+)', text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_land_zoning(self, specs: Dict[str, str]) -> Optional[str]:
        text = specs.get("land_zoning", "")
        match = re.search(r'土地分區\s+([^車位棟戶座使公建築樓建]+)', text)
        if match:
            return match.group(1).strip()
        return None

    def _parse_households(self, raw_value: Optional[str]) -> Optional[int]:
        if not raw_value:
            return None
        match = re.search(r'\d+', raw_value)
        return int(match.group()) if match else None
