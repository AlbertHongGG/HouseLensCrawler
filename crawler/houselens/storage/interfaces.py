from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum
from ..models.property import StandardProperty
from ..models.community import StandardCommunity

class CheckStatus(Enum):
    NEW = "NEW"
    DUPLICATE = "DUPLICATE"
    LIMIT_REACHED = "LIMIT_REACHED"

class IDataStorage(ABC):
    """
    Abstract Interface for data storage (Properties, Communities).
    """
    @abstractmethod
    def save(self, property_data: StandardProperty) -> bool:
        pass
        
    @abstractmethod
    def save_many(self, properties: List[StandardProperty]) -> bool:
        pass

    @abstractmethod
    def save_community(self, community_data: StandardCommunity) -> bool:
        pass

    @abstractmethod
    def find_potential_duplicates(self, property_data: StandardProperty) -> List[StandardProperty]:
        """
        Find potential duplicates in the database using fast SQL retrieval 
        (e.g., matching city, district, street, floor, ping range).
        """
        pass


class IQueueStorage(ABC):
    """
    Abstract Interface for Crawl Queue operations (Consumer Mode).
    """
    @abstractmethod
    def push_job(self, spider_name: str, url: str) -> bool:
        """Push a new URL to the queue (PENDING state)."""
        pass

    @abstractmethod
    def pop_pending_jobs(self, spider_name: str, batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Pop and lock pending jobs.
        Returns a list of dicts containing at least 'id', 'url', 'retry_count'.
        The status of these jobs should be updated to 'PROCESSING' to avoid race conditions.
        """
        pass

    @abstractmethod
    def update_job_status(self, job_id: str, status: str, result_msg: str = None) -> bool:
        """
        Update the job status (e.g., 'SUCCESS', 'FAILED').
        """
        pass


class IStorage(IDataStorage, IQueueStorage):
    """
    Unified Storage Interface combining Data and Queue operations.
    """
    pass
