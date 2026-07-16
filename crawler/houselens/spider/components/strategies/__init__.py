from .interface import ICrawlStrategy
from .full import FullCrawlStrategy
from .targeted import TargetedCrawlStrategy
from .consumer import ConsumerStrategy

__all__ = [
    'ICrawlStrategy',
    'FullCrawlStrategy',
    'TargetedCrawlStrategy'
]
