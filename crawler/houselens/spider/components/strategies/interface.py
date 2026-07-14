from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ....base import BaseSpider
    from .....engine.context import SpiderContext

class ICrawlStrategy(ABC):
    """
    爬蟲策略的抽象介面。
    實作此介面以決定 Spider 要如何走訪網頁 (例如：完整翻頁、單點特定網址等)。
    """
    @abstractmethod
    def execute(self, spider: 'BaseSpider', browser, context: 'SpiderContext') -> int:
        """
        執行策略，回傳成功處理的物件數量。
        """
        pass
