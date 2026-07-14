import re
import time
import logging

from ..base import BaseSpider
from ...models.property import StandardProperty
from .navigator import Spider591Navigator
from .profile import get_591_profile
from .transformer import Spider591Transformer
from ...engine.browser_pool import browser_manager
from ...engine.events import event_bus, Event
from ...engine.context import SpiderContext

class Spider591(BaseSpider):
    """
    591 爬蟲的裝配器 (Assembler)。
    負責將 Navigator, Profile, Transformer 裝配到 BaseSpider 骨架中。
    """

    def __init__(self, config):
        super().__init__(config)
        self.navigator = Spider591Navigator(self.platform_name)
        self.profile = get_591_profile()
        self.transformer = Spider591Transformer()

    @property
    def platform_name(self) -> str:
        return "591"
