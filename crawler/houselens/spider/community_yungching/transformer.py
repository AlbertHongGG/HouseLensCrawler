import re
from typing import Dict, Any, Optional
from ...models.community import StandardCommunity

from ..components.transformers.community import BaseCommunityTransformer

class YungchingCommunityTransformer(BaseCommunityTransformer):
    """
    Transforms raw scraped data into a StandardCommunity model for Yungching.
    """

    def transform_builder(self, raw_data: Dict[str, Any]) -> Optional[str]:
        specs = raw_data.get('specs', {})
        builder = specs.get("建設公司")
        if builder:
            builder = builder.strip()
        return builder if builder else None
