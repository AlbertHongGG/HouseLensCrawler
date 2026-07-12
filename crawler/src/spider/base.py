from abc import ABC, abstractmethod

class BaseSpider(ABC):
    """
    Base Spider class. Each Spider represents a single Task that handles
    the entire crawling process for a specific platform sequentially.
    """
    def __init__(self, config, visualizer=None):
        self.config = config
        self.visualizer = visualizer

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the name of the platform (e.g., '591', 'yungching')"""
        pass

    @abstractmethod
    def run(self):
        """
        Executes the entire crawling logic for this platform.
        Handles its own pagination and item loops sequentially.
        """
        pass
