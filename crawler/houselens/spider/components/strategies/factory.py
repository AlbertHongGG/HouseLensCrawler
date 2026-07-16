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
    def create(mode: CrawlMode, config=None, **kwargs: Any) -> ICrawlStrategy:
        storage = StorageProvider.get_storage()
        
        if mode == CrawlMode.FULL:
            return FullCrawlStrategy()
        elif mode == CrawlMode.TARGETED:
            if not config or not config.target_urls:
                raise ValueError(f"TARGETED mode requires '{config.platform_name}_TARGET_URLS' in .env")
            return TargetedCrawlStrategy(config.target_urls)
        elif mode == CrawlMode.CONSUMER:
            return ConsumerStrategy(queue_storage=storage, **kwargs)
        else:
            raise ValueError(f"Unknown crawl mode: {mode}")
