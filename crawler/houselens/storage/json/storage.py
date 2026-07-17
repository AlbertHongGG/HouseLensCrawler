import json
import os
import threading
import logging

from ..interfaces import IStorage
from ...config import AppConfig

from .mixins.property import JsonPropertyMixin
from .mixins.community import JsonCommunityMixin
from .mixins.dedup import JsonDedupMixin
from .mixins.queue import JsonQueueMixin

def _ensure_dir(filepath: str):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

class JsonStorage(JsonPropertyMixin, JsonCommunityMixin, JsonDedupMixin, JsonQueueMixin, IStorage):
    """
    Unified local JSON-based storage that mirrors Supabase architecture.
    Composed of Mixins for separation of concerns.
    """
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        
        storage_dir = os.path.join(base_dir, AppConfig.JSON_STORAGE_PATH)
        
        # Tables (Files)
        self.data_filepath = os.path.join(storage_dir, "property.jsonl")
        self.community_filepath = os.path.join(storage_dir, "community.jsonl")
        self.builder_filepath = os.path.join(storage_dir, "builder.json")
        self.community_builder_filepath = os.path.join(storage_dir, "community_builders.json")
        self.dedup_filepath = os.path.join(storage_dir, "crawler_dedup.json")
        self.queue_filepath = os.path.join(storage_dir, "crawl_queue.json")
        
        # Internal states
        self._dedup_list = []
        self._seen_items = {} # For fast lookup O(1)
        
        self._queue = []
        self._builders = []
        self._community_builders = []
        
        # Locks
        self._dedup_lock = threading.Lock()
        self._queue_lock = threading.Lock()
        self._builder_lock = threading.Lock()
        self._community_builder_lock = threading.Lock()
        
        _ensure_dir(self.data_filepath)
        _ensure_dir(self.community_filepath)
        _ensure_dir(self.builder_filepath)
        _ensure_dir(self.community_builder_filepath)
        _ensure_dir(self.dedup_filepath)
        _ensure_dir(self.queue_filepath)
        
        self._load_dedup()
        self._load_queue()
        self._load_builder()
        self._load_community_builder()

    # --- Loading & Saving internal helpers ---
    def _load_builder(self):
        if os.path.exists(self.builder_filepath):
            try:
                with open(self.builder_filepath, "r", encoding="utf-8") as f:
                    self._builders = json.load(f)
            except Exception:
                self._builders = []

    def _save_builder(self):
        try:
            with open(self.builder_filepath, "w", encoding="utf-8") as f:
                json.dump(self._builders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving builder.json: {e}")

    def _load_community_builder(self):
        if os.path.exists(self.community_builder_filepath):
            try:
                with open(self.community_builder_filepath, "r", encoding="utf-8") as f:
                    self._community_builders = json.load(f)
            except Exception:
                self._community_builders = []

    def _save_community_builder(self):
        try:
            with open(self.community_builder_filepath, "w", encoding="utf-8") as f:
                json.dump(self._community_builders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving community_builders.json: {e}")

    def _load_dedup(self):
        if os.path.exists(self.dedup_filepath):
            try:
                with open(self.dedup_filepath, "r", encoding="utf-8") as f:
                    self._dedup_list = json.load(f)
                    self._seen_items = {
                        f"{item.get('source_platform')}_{item.get('entity_type')}_{item.get('source_id')}": True 
                        for item in self._dedup_list
                    }
            except Exception:
                self._dedup_list = []
                self._seen_items = {}

    def _save_dedup(self):
        try:
            with open(self.dedup_filepath, "w", encoding="utf-8") as f:
                json.dump(self._dedup_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving crawler_dedup.json: {e}")

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
            logging.error(f"Error saving crawl_queue.json: {e}")
