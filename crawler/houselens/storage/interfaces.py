from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum
from ..models.property import StandardProperty

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
    def save_community(self, community_data: Any) -> bool:
        pass


class IDedupStorage(ABC):
    """
    Abstract Interface for Deduplication tracking.
    """
    @abstractmethod
    def check_and_register(self, source_id: str, current_url: str, entity_type: str = 'property', source_platform: str = 'unknown') -> Tuple[CheckStatus, str]:
        """
        Check if an item exists.
        If it's new, register it and return (CheckStatus.NEW, current_url).
        If duplicate, return (CheckStatus.DUPLICATE, original_url).
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
    def update_job_status(self, job_id: str, status: str, retry_count: int) -> bool:
        """
        Update the status of a job (e.g., COMPLETED, FAILED, or PENDING on retry).
        """
        pass

class IStorage(IDataStorage, IDedupStorage, IQueueStorage):
    """
    Unified Storage Interface combining Data, Dedup, and Queue operations.
    """
    pass
