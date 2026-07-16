from typing import Any
from .interface import ICrawlStrategy
from .full import FullCrawlStrategy
from .targeted import TargetedCrawlStrategy
from .consumer import ConsumerStrategy
from ....config import CrawlMode
from ....storage.provider import StorageProvider

class StrategyFactory:
    """
    爬蟲策略工廠 (Strategy Factory)。
    根據傳入的 CrawlMode 動態生成對應的策略實體，將策略的建構邏輯與主程式解耦。
    """
    @staticmethod
    def create(mode: CrawlMode, **kwargs: Any) -> ICrawlStrategy:
        if mode == CrawlMode.FULL:
            return FullCrawlStrategy()
        elif mode == CrawlMode.TARGETED:
            target_urls = kwargs.get('target_urls')
            if not target_urls:
                raise ValueError("TARGETED mode requires 'target_urls' argument.")
            return TargetedCrawlStrategy(target_urls)
        elif mode == CrawlMode.CONSUMER:
            storage = StorageProvider.get_storage()
            return ConsumerStrategy(queue_storage=storage, **kwargs)
        else:
            raise ValueError(f"Unknown crawl mode: {mode}")
