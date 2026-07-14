from typing import Any
from .interface import ICrawlStrategy
from .full import FullCrawlStrategy
from .targeted import TargetedCrawlStrategy
from ....config import CrawlMode

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
        else:
            raise ValueError(f"Unknown crawl mode: {mode}")
