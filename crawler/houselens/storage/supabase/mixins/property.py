import logging
from typing import List
from ....models.property import StandardProperty

class SupabasePropertyMixin:
    """
    Mixin for Property related Supabase storage operations.
    Requires `self.client` to be defined in the main class.
    """
    def save(self, property_data: StandardProperty) -> bool:
        try:
            data = property_data.model_dump(exclude_none=True)
            response = self.client.table("property").upsert(data).execute()
            
            if response.data:
                logging.info(f"[SupabaseStorage] Successfully saved property {property_data.property_uuid}")
                return True
            else:
                logging.warning(f"[SupabaseStorage] Failed to save property {property_data.property_uuid} - {response}")
                return False
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error saving property: {e}")
            return False

    def save_many(self, properties: List[StandardProperty]) -> bool:
        if not properties:
            return True
            
        try:
            data = [p.model_dump(exclude_none=True) for p in properties]
            response = self.client.table("property").upsert(data).execute()
            
            if response.data:
                logging.info(f"[SupabaseStorage] Successfully saved {len(properties)} properties in batch.")
                return True
            else:
                logging.warning(f"[SupabaseStorage] Failed to save batch properties - {response}")
                return False
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error saving batch properties: {e}")
            return False
