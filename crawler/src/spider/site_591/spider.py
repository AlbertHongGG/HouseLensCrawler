import re
import time
import logging

from ..base import BaseSpider
from ...models.property import StandardProperty
from .navigator import Spider591Navigator
from .locator import Spider591Locator
from .parser import Spider591Parser
from ...engine.browser_pool import browser_manager
from ...engine.events import event_bus, Event
from ...engine.context import SpiderContext

class Spider591(BaseSpider):
    """
    591 爬蟲的裝配器 (Assembler)。
    負責將 Navigator, Locator, Parser 裝配到 BaseSpider 骨架中。
    """

    def __init__(self, config):
        super().__init__(config)
        self.navigator = Spider591Navigator(self.platform_name)
        self.locator = Spider591Locator()
        self.parser = Spider591Parser(self.platform_name)

    @property
    def platform_name(self) -> str:
        return "591"
