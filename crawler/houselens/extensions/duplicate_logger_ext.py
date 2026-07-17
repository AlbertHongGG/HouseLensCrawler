import json
import os
import logging
import threading
from ..engine.events import event_bus, Event
from ..models.dedup import DuplicateRecord

class DuplicateLoggerExtension:
    """
    監聽重複事件並將紀錄寫入 data/duplicates.jsonl 的擴充套件。
    """
    def __init__(self, data_dir: str = "data"):
        self.output_file = os.path.join(data_dir, "duplicates.jsonl")
        self._lock = threading.Lock()
        
        # Ensure directory exists
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # 訂閱事件
        event_bus.subscribe(Event.DUPLICATE_DETECTED, self.on_duplicate)
        logging.info("[Extension] DuplicateLoggerExtension registered.")

    def on_duplicate(self, platform: str, source_id: str, url_a: str, url_b: str):
        record = DuplicateRecord(
            platform=platform,
            source_id=source_id,
            url_a=url_a,
            url_b=url_b
        )
        
        try:
            with self._lock:
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    f.write(record.model_dump_json() + '\n')
        except Exception as e:
            logging.error(f"[DuplicateLogger] Failed to write duplicate record: {e}")
