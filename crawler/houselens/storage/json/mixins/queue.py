from typing import List, Dict, Any

class JsonQueueMixin:
    """
    Mixin for Crawl Queue related JSON storage operations.
    Requires `self.queue_filepath`, `self._queue`, 
    and `self._queue_lock` to be defined in the main class.
    """
    
    def push_job(self, spider_name: str, url: str) -> bool:
        with self._queue_lock:
            if any(q['url'] == url and q['spider_name'] == spider_name for q in self._queue):
                return True
            
            job_id = str(len(self._queue) + 1)
            self._queue.append({
                "id": job_id,
                "spider_name": spider_name,
                "url": url,
                "status": "PENDING",
                "retry_count": 0
            })
            self._save_queue()
            return True

    def pop_pending_jobs(self, spider_name: str, batch_size: int = 10) -> List[Dict[str, Any]]:
        with self._queue_lock:
            pending = [q for q in self._queue if q['spider_name'] == spider_name and q['status'] == "PENDING"]
            batch = pending[:batch_size]
            for job in batch:
                job['status'] = "PROCESSING"
            self._save_queue()
            return batch

    def update_job_status(self, job_id: str, status: str, retry_count: int) -> bool:
        with self._queue_lock:
            for job in self._queue:
                if job['id'] == job_id:
                    job['status'] = status
                    job['retry_count'] = retry_count
                    self._save_queue()
                    return True
            return False
