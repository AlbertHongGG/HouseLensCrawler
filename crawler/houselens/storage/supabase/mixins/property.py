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

    def find_potential_duplicates(self, property_data: StandardProperty) -> List[StandardProperty]:
        if not property_data.city or not property_data.district or not property_data.street:
            return []

        try:
            # Query properties in the same city, district, street
            res = self.client.table('property') \
                .select('*') \
                .eq('city', property_data.city) \
                .eq('district', property_data.district) \
                .eq('street', property_data.street) \
                .execute()

            if not res.data:
                return []

            candidates = []
            for item in res.data:
                try:
                    c = StandardProperty(**item)
                    candidates.append(c)
                except Exception:
                    pass

            # Filter candidates by basic ping bounds to avoid passing too many to scorer
            filtered_candidates = []
            target_ping = property_data.building_ping
            for c in candidates:
                if target_ping > 0 and c.building_ping > 0:
                    diff_ratio = abs(c.building_ping - target_ping) / target_ping
                    if diff_ratio <= 0.05: # within 5% diff
                        filtered_candidates.append(c)
                else:
                    filtered_candidates.append(c)
            
            return filtered_candidates
            
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error finding potential duplicates: {e}")
            return []
