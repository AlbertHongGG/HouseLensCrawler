import time
import logging
from typing import List, Dict, Any
from DrissionPage import ChromiumPage

from .navigator import SpiderYungchingNavigator
from .locator import SpiderYungchingLocator
from .parser import SpiderYungchingParser
from ..base import BaseSpider
from ...config import SpiderConfig
from ...engine.events import event_bus, Event

class YungchingSpider(BaseSpider):
    """
    永慶房屋爬蟲的裝配器 (Assembler)。
    負責將 Navigator, Locator, Parser 裝配到 BaseSpider 骨架中。
    """
    
    def __init__(self, config: SpiderConfig):
        super().__init__(config)
        self.navigator = SpiderYungchingNavigator(self.platform_name)
        self.locator = SpiderYungchingLocator()
        self.parser = SpiderYungchingParser()

    @property
    def platform_name(self) -> str:
        return "yungching"
