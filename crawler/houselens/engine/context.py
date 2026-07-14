import threading

from typing import Tuple
from .dedup import DedupManager, CheckStatus

class EngineContext:
    """
    Manages the global state and lifecycle of the entire execution engine.
    """
    def __init__(self):
        self._shutdown_event = threading.Event()
        self.dedup_manager = DedupManager()

    def cancel(self):
        """Signals all spiders to stop executing."""
        self._shutdown_event.set()

    def is_cancelled(self) -> bool:
        """Checks if the engine is shutting down."""
        return self._shutdown_event.is_set()


class SpiderContext:
    """
    Context provided to each individual Spider.
    Wraps the EngineContext to allow checking for cancellation, and maintains
    spider-specific thread-safe state like item limits and deduplication.
    """
    def __init__(self, engine_context: EngineContext, max_items: int):
        self._engine_context = engine_context
        self._max_items = max_items
        
        self._lock = threading.Lock()
        self._items_collected = 0

    def is_cancelled(self) -> bool:
        """Check if the spider should stop running due to engine shutdown."""
        return self._engine_context.is_cancelled()

    def register_item(self, source_id: str, url: str) -> Tuple[CheckStatus, str]:
        """
        Registers an item and checks if we haven't reached the limit or if it's a duplicate.
        """
        with self._lock:
            if self._items_collected >= self._max_items:
                return CheckStatus.LIMIT_REACHED, ""
            
            status, original_url = self._engine_context.dedup_manager.check_and_register(source_id, url)
            
            if status == CheckStatus.NEW:
                self._items_collected += 1
                
            return status, original_url

    def reached_limit(self) -> bool:
        """Check if the spider has reached its max items limit."""
        with self._lock:
            return self._items_collected >= self._max_items

    def get_items_collected(self) -> int:
        with self._lock:
            return self._items_collected
