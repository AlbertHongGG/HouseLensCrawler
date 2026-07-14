import logging
import time
import re
from typing import List

from ..base import BaseSpider
from ..factory import SpiderFactory
from .navigator import SinyiNavigator
from .profile import get_sinyi_profile
from .transformer import SpiderSinyiTransformer
from ...models.property import StandardProperty
from ...engine.events import event_bus, Event

@SpiderFactory.register('sinyi')
class SinyiSpider(BaseSpider):
    @property
    def platform_name(self) -> str:
        return "sinyi"

    def __init__(self, config):
        super().__init__(config)
        self.navigator = SinyiNavigator(self.platform_name)
        self.profile = get_sinyi_profile()
        self.transformer = SpiderSinyiTransformer()
