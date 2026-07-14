import json
import os
from typing import List
from .base import IDataStorage
from ..models.property import StandardProperty
from .factory import StorageFactory
from ..config import AppConfig

@StorageFactory.register("json")
class JsonStorage(IDataStorage):
    """
    Storage implementation that appends data to a JSON Lines (JSONL) file.
    Using JSONL makes it thread-safe for appending and avoids reading the whole 
    file into memory.
    """
    def __init__(self):
        json_path = AppConfig.JSON_STORAGE_PATH
        # Resolve to project root (2 levels up from src/storage)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.filepath = os.path.join(base_dir, json_path)
        self._ensure_dir()

    def _ensure_dir(self):
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def save(self, property_data: StandardProperty) -> bool:
        try:
            with open(self.filepath, 'a', encoding='utf-8') as f:
                # model_dump_json is available in pydantic v2
                json_str = property_data.model_dump_json()
                f.write(json_str + '\n')
            return True
        except Exception as e:
            print(f"Error saving to JSONL: {e}")
            return False

    def save_many(self, properties: List[StandardProperty]) -> bool:
        try:
            with open(self.filepath, 'a', encoding='utf-8') as f:
                for prop in properties:
                    json_str = prop.model_dump_json()
                    f.write(json_str + '\n')
            return True
        except Exception as e:
            print(f"Error saving multiple to JSONL: {e}")
            return False
