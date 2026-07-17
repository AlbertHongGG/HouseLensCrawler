import logging
from typing import List
from ....models.property import StandardProperty

class JsonPropertyMixin:
    """
    Mixin for Property related JSON storage operations.
    Requires `self.data_filepath` to be defined in the main class.
    """
    def save(self, property_data: StandardProperty) -> bool:
        try:
            with open(self.data_filepath, 'a', encoding='utf-8') as f:
                f.write(property_data.model_dump_json(exclude_none=True) + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving to property.jsonl: {e}")
            return False

    def save_many(self, properties: List[StandardProperty]) -> bool:
        try:
            with open(self.data_filepath, 'a', encoding='utf-8') as f:
                for prop in properties:
                    f.write(prop.model_dump_json(exclude_none=True) + '\n')
            return True
        except Exception as e:
            logging.error(f"Error saving multiple to property.jsonl: {e}")
            return False

    def find_potential_duplicates(self, property_data: StandardProperty) -> List[StandardProperty]:
        if not property_data.city or not property_data.district:
            return []

        candidates = []
        target_ping = property_data.building_ping
        
        try:
            import json
            with open(self.data_filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    # Fast string check before parsing JSON
                    if property_data.district not in line:
                        continue
                        
                    item = json.loads(line)
                    if item.get('city') == property_data.city and item.get('district') == property_data.district:
                        c_ping = item.get('building_ping', 0)
                        if target_ping > 0 and c_ping > 0:
                            diff_ratio = abs(c_ping - target_ping) / target_ping
                            if diff_ratio <= 0.05:
                                try:
                                    candidates.append(StandardProperty(**item))
                                except Exception:
                                    pass
                        else:
                            try:
                                candidates.append(StandardProperty(**item))
                            except Exception:
                                pass
        except FileNotFoundError:
            pass
        except Exception as e:
            logging.error(f"[JsonStorage] Error in find_potential_duplicates: {e}")
            
        return candidates
