import json
import os
import threading
import logging
from typing import List, Tuple, Dict, Any

from ..interfaces import IStorage, CheckStatus
from ...models.property import StandardProperty
from ...config import AppConfig

def _ensure_dir(filepath: str):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

class JsonStorage(IStorage):
    """
    Unified local JSON-based storage for Data, Dedup, and Queue.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Data paths
        self.data_filepath = os.path.join(base_dir, AppConfig.JSON_STORAGE_PATH)
        self.community_filepath = os.path.join(base_dir, "data/communities.jsonl")
        
        # Dedup paths & state
        self.dedup_filepath = os.path.join(base_dir, "data/seen_items.json")
        self._seen_items = {}
        
        # Queue paths & state
        self.queue_filepath = os.path.join(base_dir, "data/crawl_queue.json")
        self._queue = []
        
        # Locks
        self._dedup_lock = threading.Lock()
        self._queue_lock = threading.Lock()
        
        _ensure_dir(self.data_filepath)
        _ensure_dir(self.community_filepath)
        _ensure_dir(self.dedup_filepath)
        _ensure_dir(self.queue_filepath)
        
        self._load_dedup()
        self._load_queue()

    # --- DataStorage Implementation ---
    def save(self, property_data: StandardProperty) -> bool:
        try:
            with open(self.data_filepath, 'a', encoding='utf-8') as f:
                f.write(property_data.model_dump_json() + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving to JSONL: {e}")
            return False

    def save_many(self, properties: List[StandardProperty]) -> bool:
        try:
            with open(self.data_filepath, 'a', encoding='utf-8') as f:
                for prop in properties:
                    f.write(prop.model_dump_json() + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving multiple to JSONL: {e}")
            return False

    def save_community(self, community_data: Any) -> bool:
        try:
            with open(self.community_filepath, 'a', encoding='utf-8') as f:
                if hasattr(community_data, 'model_dump_json'):
                    json_str = community_data.model_dump_json()
                else:
                    json_str = json.dumps(community_data, ensure_ascii=False)
                f.write(json_str + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving community to JSONL: {e}")
            return False

    # --- DedupStorage Implementation ---
    def _load_dedup(self):
        if os.path.exists(self.dedup_filepath):
            try:
                with open(self.dedup_filepath, "r", encoding="utf-8") as f:
                    self._seen_items = json.load(f)
            except Exception:
                self._seen_items = {}

    def _save_dedup(self):
        try:
            with open(self.dedup_filepath, "w", encoding="utf-8") as f:
                json.dump(self._seen_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving dedup items: {e}")

    def check_and_register(self, source_id: str, current_url: str, entity_type: str = 'property', source_platform: str = 'unknown') -> Tuple[CheckStatus, str]:
        key = f"{source_platform}_{entity_type}_{source_id}"
        with self._dedup_lock:
            if key in self._seen_items:
                return CheckStatus.DUPLICATE, self._seen_items[key]
            else:
                self._seen_items[key] = current_url
                self._save_dedup()
                return CheckStatus.NEW, current_url

    # --- QueueStorage Implementation ---
    def _load_queue(self):
        if os.path.exists(self.queue_filepath):
            try:
                with open(self.queue_filepath, "r", encoding="utf-8") as f:
                    self._queue = json.load(f)
            except Exception:
                self._queue = []

    def _save_queue(self):
        try:
            with open(self.queue_filepath, "w", encoding="utf-8") as f:
                json.dump(self._queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving queue items: {e}")

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
