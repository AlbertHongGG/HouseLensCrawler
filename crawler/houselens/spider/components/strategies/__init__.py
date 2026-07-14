from .interface import ICrawlStrategy
from .full import FullCrawlStrategy
from .targeted import TargetedCrawlStrategy

__all__ = [
    'ICrawlStrategy',
    'FullCrawlStrategy',
    'TargetedCrawlStrategy'
]
