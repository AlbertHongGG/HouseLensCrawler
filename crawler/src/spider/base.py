from abc import ABC, abstractmethod

class BaseSpider(ABC):
    """
    Base Spider class. Each Spider represents a single Task that handles
    the entire crawling process for a specific platform sequentially.
    """
    def __init__(self, config):
        self.config = config

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the name of the platform (e.g., '591', 'yungching')"""
        pass

    @abstractmethod
    def run(self, context):
        """
        Executes the entire crawling logic for this platform.
        Handles its own pagination and item loops sequentially, and checks context for cancellation.
        """
        pass
