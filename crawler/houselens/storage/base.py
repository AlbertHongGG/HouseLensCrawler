from abc import ABC, abstractmethod
from typing import List
from ..models.property import StandardProperty

class IDataStorage(ABC):
    """
    Abstract Interface for data storage.
    Allows easy switching between JSON, Database, or other formats.
    """
    
    @abstractmethod
    def save(self, property_data: StandardProperty) -> bool:
        """
        Saves a single property record.
        Returns True if successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def save_many(self, properties: List[StandardProperty]) -> bool:
        """
        Saves a batch of property records.
        """
        pass
