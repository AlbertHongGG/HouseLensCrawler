from .spider import YungchingSpider
from ..factory import SpiderFactory

SpiderFactory.register("yungching")(YungchingSpider)
