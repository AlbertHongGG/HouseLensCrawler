import time
import logging
from typing import List, Dict, Any
from DrissionPage import ChromiumPage

from .navigator import SpiderYungchingNavigator
from .profile import get_yungching_profile
from .transformer import SpiderYungchingTransformer
from ..base import BaseSpider
from ...config import SpiderConfig
from ...engine.events import event_bus, Event

class YungchingSpider(BaseSpider):
    """
    永慶房屋爬蟲的裝配器 (Assembler)。
    負責將 Navigator, Profile, Transformer 裝配到 BaseSpider 骨架中。
    """
    
    def __init__(self, config: SpiderConfig):
        super().__init__(config)
        self.navigator = SpiderYungchingNavigator(self.platform_name)
        self.profile = get_yungching_profile()
        self.transformer = SpiderYungchingTransformer()

    @property
    def platform_name(self) -> str:
        return "yungching"
