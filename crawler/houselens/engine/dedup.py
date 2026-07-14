import json
import os
import logging
from enum import Enum
from typing import Dict, Tuple

class CheckStatus(Enum):
    NEW = "NEW"
    DUPLICATE = "DUPLICATE"
    LIMIT_REACHED = "LIMIT_REACHED"

class DedupManager:
    """
    持久化去重中心 (Persistent Deduplication Manager)
    負責維護已抓取過的物件，並提供持久化存檔。
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.seen_file_path = os.path.join(self.data_dir, "seen_items.json")
        self._seen_items: Dict[str, str] = {}
        
        # 確保資料夾存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self._load_seen_items()

    def _load_seen_items(self):
        if os.path.exists(self.seen_file_path):
            try:
                with open(self.seen_file_path, "r", encoding="utf-8") as f:
                    self._seen_items = json.load(f)
                logging.info(f"[DedupManager] Loaded {len(self._seen_items)} seen items from disk.")
            except Exception as e:
                logging.error(f"[DedupManager] Error loading seen items: {e}")
                self._seen_items = {}

    def _save_seen_items(self):
        try:
            with open(self.seen_file_path, "w", encoding="utf-8") as f:
                json.dump(self._seen_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"[DedupManager] Error saving seen items: {e}")

    def check_and_register(self, source_id: str, current_url: str) -> Tuple[CheckStatus, str]:
        """
        檢查物件是否為重複。
        若是新物件，則註冊並回傳 (NEW, current_url)。
        若是重複物件，則回傳 (DUPLICATE, original_url)。
        """
        if source_id in self._seen_items:
            original_url = self._seen_items[source_id]
            return CheckStatus.DUPLICATE, original_url
        else:
            self._seen_items[source_id] = current_url
            self._save_seen_items() # 可以改成定期儲存，但為了保證不遺失先同步儲存
            return CheckStatus.NEW, current_url
