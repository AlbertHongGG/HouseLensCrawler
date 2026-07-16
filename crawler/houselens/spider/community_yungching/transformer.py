import re
from typing import Dict, Any, Optional
from ...models.community import StandardCommunity


class YungchingCommunityTransformer:
    """
    Transforms raw scraped data into a StandardCommunity model for Yungching.
    """

    def transform(self, raw_data: Dict[str, Any]) -> StandardCommunity:
        source_id = raw_data['source_id']
        specs = raw_data.get('specs', {})

        return StandardCommunity(
            community_uuid=f"yungching_{source_id}",
            source_platform="yungching",
            source_id=source_id,
            url=raw_data['url'],
            name=raw_data['name'],
            address=raw_data.get('address'),
            builder=self._extract_builder(specs),
            completion_date=specs.get("完工日期") or specs.get("屋齡"),
            total_households=self._parse_households(specs.get("總戶數")),
            building_structure=specs.get("主結構") or specs.get("構造"),
            land_zoning=specs.get("土地使用分區"),
        )

    def _extract_builder(self, specs: Dict[str, str]) -> Optional[str]:
        builder = specs.get("建設公司")
        if builder:
            builder = builder.strip()
        return builder if builder else None

    def _parse_households(self, raw_value: Optional[str]) -> Optional[int]:
        if not raw_value:
            return None
        match = re.search(r'\d+', raw_value)
        return int(match.group()) if match else None
