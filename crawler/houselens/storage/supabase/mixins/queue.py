import logging
from typing import List, Dict, Any

class SupabaseQueueMixin:
    """
    Mixin for Crawl Queue related Supabase storage operations.
    Requires `self.client` to be defined in the main class.
    """
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
