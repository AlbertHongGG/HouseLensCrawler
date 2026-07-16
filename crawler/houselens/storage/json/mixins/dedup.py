from typing import Tuple
from ...interfaces import CheckStatus

class JsonDedupMixin:
    """
    Mixin for Deduplication related JSON storage operations.
    Requires `self.dedup_filepath`, `self._dedup_list`, `self._seen_items`, 
    and `self._dedup_lock` to be defined in the main class.
    """
    
    def check_and_register(self, source_id: str, current_url: str, entity_type: str = 'property', source_platform: str = 'unknown') -> Tuple[CheckStatus, str]:
        key = f"{source_platform}_{entity_type}_{source_id}"
        with self._dedup_lock:
            if key in self._seen_items:
                return CheckStatus.DUPLICATE, current_url
            else:
                self._seen_items[key] = True
                self._dedup_list.append({
                    "source_platform": source_platform,
                    "source_id": source_id,
                    "entity_type": entity_type
                })
                self._save_dedup()
                return CheckStatus.NEW, current_url
