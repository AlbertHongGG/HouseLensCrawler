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
                
            builder_ids = []
            
            if builder_name:
                import re
                # 將「宏泰人壽開發、宏盛建設、達欣工程」透過正規表達式切開
                # 支援分隔符號: 全形/半形逗號, 頓號, 斜線, 空白
                names = [n.strip() for n in re.split(r'[、,，/ ]+', builder_name) if n.strip()]
                
                with self._builder_lock:
                    for name in names:
                        existing = next((b for b in self._builders if b['name'] == name), None)
                        if existing:
                            builder_ids.append(existing['builder_id'])
                        else:
                            new_builder_id = str(uuid.uuid4())
                            self._builders.append({
                                "builder_id": new_builder_id,
                                "name": name,
                                "group_id": None
                            })
                            builder_ids.append(new_builder_id)
                            logging.info(f"[JsonStorage] Auto-created new builder: {name}")
                    self._save_builder()
            
            community_uuid = community_dict.get('community_uuid', str(uuid.uuid4()))
            
            # 建立多對多關聯 (Many-to-Many Mapping)
            if builder_ids:
                with self._community_builder_lock:
                    for b_id in builder_ids:
                        # 避免重複關聯
                        exists = any(m['community_uuid'] == community_uuid and m['builder_id'] == b_id 
                                     for m in self._community_builders)
                        if not exists:
                            self._community_builders.append({
                                "id": str(uuid.uuid4()),
                                "community_uuid": community_uuid,
                                "builder_id": b_id
                            })
                    self._save_community_builder()
                
            # 將原本的 community 資料存入 JSONL (不再有 builder_id，只有 builder_name_raw)
            with open(self.community_filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(community_dict, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving community.jsonl: {e}", exc_info=True)
            return False
