import logging
from typing import List, Tuple, Dict, Any
from ..interfaces import IStorage, CheckStatus
from ...models.property import StandardProperty
from .client import SupabaseClientManager
class SupabaseStorage(IStorage):
    """
    Storage implementation that saves data directly to Supabase PostgREST API.
    """
    def __init__(self):
        self.client = SupabaseClientManager.get_client()

    def save(self, property_data: StandardProperty) -> bool:
        """
        Save a single property to Supabase.
        """
        try:
            data = property_data.model_dump(exclude_none=True)
            # The UUID fields are mapped directly
            # For JSONB raw_data, if it exists in the model we can pass it, 
            # but currently StandardProperty has no raw_data field.
            
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
        """
        Save multiple properties to Supabase in a batch.
        """
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

    def save_community(self, community_data: 'StandardCommunity') -> bool:
        """
        Save community data to Supabase.
        If builder exists, it maps to builder_name_raw and auto-creates builder.
        """
        try:
            from ..models.community import StandardCommunity
            if isinstance(community_data, StandardCommunity):
                community_dict = community_data.model_dump(exclude_none=True)
            else:
                community_dict = community_data
            
            builder_name = community_dict.pop('builder', None)
            if builder_name:
                community_dict['builder_name_raw'] = builder_name
            builder_id = None
            
            # Auto-create builder if we have a name
            if builder_name:
                # 1. Try to find the builder
                b_res = self.client.table("builder").select("builder_id").eq("name", builder_name).execute()
                
                if b_res.data and len(b_res.data) > 0:
                    builder_id = b_res.data[0]['builder_id']
                else:
                    # 2. Insert new builder
                    # The Postgres Trigger trg_match_builder_group will auto-assign group_id!
                    insert_res = self.client.table("builder").insert({"name": builder_name}).execute()
                    if insert_res.data:
                        builder_id = insert_res.data[0]['builder_id']
                        logging.info(f"[SupabaseStorage] Auto-created new builder: {builder_name}")
            
            # Update the community data with the builder_id
            if builder_id:
                community_dict['builder_id'] = builder_id
                
            response = self.client.table("community").upsert(community_dict).execute()
            
            if response.data:
                logging.info(f"[SupabaseStorage] Successfully saved community {community_dict.get('community_uuid')}")
                return True
            else:
                return False
                
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error saving community: {e}")
            return False

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

    def push_job(self, spider_name: str, url: str) -> bool:
        try:
            res = self.client.table('crawl_queue').insert({
                'spider_name': spider_name,
                'url': url,
                'status': 'PENDING',
                'retry_count': 0
            }).execute()
            return True if res.data else False
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                return True
            logging.error(f"[SupabaseStorage] Error pushing to queue: {e}")
            return False

    def pop_pending_jobs(self, spider_name: str, batch_size: int = 10) -> List[Dict[str, Any]]:
        try:
            res = self.client.table("crawl_queue") \
                .select("id, url, retry_count") \
                .eq("spider_name", spider_name) \
                .eq("status", "PENDING") \
                .limit(batch_size) \
                .execute()
            
            pending_jobs = res.data
            for job in pending_jobs:
                self.client.table("crawl_queue").update({"status": "PROCESSING"}).eq("id", job['id']).execute()
            return pending_jobs
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error popping jobs: {e}")
            return []

    def update_job_status(self, job_id: str, status: str, retry_count: int) -> bool:
        try:
            self.client.table("crawl_queue").update({
                "status": status,
                "retry_count": retry_count
            }).eq("id", job_id).execute()
            return True
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error updating job status: {e}")
            return False
