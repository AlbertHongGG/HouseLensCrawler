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
