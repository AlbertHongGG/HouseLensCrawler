import threading

class GlobalState:
    """
    Thread-safe state manager for deduplication and global limits.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.seen_items = set()
        self.items_collected = 0

    def add_and_check(self, item_id: str, max_items: int) -> bool:
        """
        Adds an item to the seen set and checks if we haven't reached the limit.
        Returns True if the item is NEW and we are UNDER the limit.
        Returns False if the item is a DUPLICATE or we EXCEEDED the limit.
        """
        with self._lock:
            if self.items_collected >= max_items:
                return False
            
            if item_id in self.seen_items:
                return False
                
            self.seen_items.add(item_id)
            self.items_collected += 1
            return True

    def reached_limit(self, max_items: int) -> bool:
        with self._lock:
            return self.items_collected >= max_items

    def get_items_collected(self) -> int:
        with self._lock:
            return self.items_collected

# Global singleton instance
global_state = GlobalState()
