import logging
from typing import Tuple
from ...interfaces import CheckStatus

class SupabaseDedupMixin:
    """
    Mixin for Deduplication related Supabase storage operations.
    Requires `self.client` to be defined in the main class.
    """
    def check_and_register(self, source_id: str, current_url: str, entity_type: str = 'property', source_platform: str = 'unknown') -> Tuple[CheckStatus, str]:
        try:
            res = self.client.table('crawler_dedup') \
                .select('id') \
                .eq('source_platform', source_platform) \
                .eq('source_id', source_id) \
                .eq('entity_type', entity_type) \
                .execute()
                
            if res.data and len(res.data) > 0:
                return CheckStatus.DUPLICATE, current_url
                
            insert_res = self.client.table('crawler_dedup').insert({
                'source_platform': source_platform,
                'source_id': source_id,
                'entity_type': entity_type
            }).execute()
            
            if insert_res.data:
                return CheckStatus.NEW, current_url
            else:
                logging.error(f"[SupabaseStorage] Failed to register dedup {source_id}")
                return CheckStatus.NEW, current_url
                
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                return CheckStatus.DUPLICATE, current_url
            logging.error(f"[SupabaseStorage] Error checking dedup: {e}")
            return CheckStatus.NEW, current_url
