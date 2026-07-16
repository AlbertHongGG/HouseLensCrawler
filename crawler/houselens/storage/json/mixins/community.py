import json
import logging
import uuid
from typing import Any

class JsonCommunityMixin:
    """
    Mixin for Community and Builder related JSON storage operations.
    Requires `self.community_filepath`, `self.builder_filepath`, `self._builders`, 
    and `self._builder_lock` to be defined in the main class.
    """
    
    def save_community(self, community_data: Any) -> bool:
        try:
            from ....models.community import StandardCommunity
            if isinstance(community_data, StandardCommunity):
                community_dict = community_data.model_dump(exclude_none=True)
            else:
                community_dict = community_data
                
            builder_name = community_dict.pop('builder', None)
            if builder_name:
                community_dict['builder_name_raw'] = builder_name
                
            builder_id = None
            if builder_name:
                with self._builder_lock:
                    existing = next((b for b in self._builders if b['name'] == builder_name), None)
                    if existing:
                        builder_id = existing['builder_id']
                    else:
                        builder_id = str(uuid.uuid4())
                        self._builders.append({
                            "builder_id": builder_id,
                            "name": builder_name,
                            "group_id": None
                        })
                        self._save_builder()
                        logging.info(f"[JsonStorage] Auto-created new builder: {builder_name}")
                        
            if builder_id:
                community_dict['builder_id'] = builder_id
                
            with open(self.community_filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(community_dict, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving community.jsonl: {e}")
            return False
