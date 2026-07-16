import re
import time
import logging
from typing import Optional, Dict, Any

from ..base import BaseSpider
from ..factory import SpiderFactory
from ...engine.events import event_bus, Event
from ...engine.context import SpiderContext
from ...storage.interfaces import CheckStatus
from .navigator import SinyiCommunityNavigator
from .transformer import SinyiCommunityTransformer


@SpiderFactory.register("sinyi_community")
class SinyiCommunitySpider(BaseSpider):
    """
    信義房屋 - 社區資料爬蟲
    遵守 Container-based Locating 原則：先定位區塊，再往下尋找元素。
    """

    def __init__(self, config, **kwargs):
        super().__init__(config)
        self.navigator = SinyiCommunityNavigator()
        self.transformer = SinyiCommunityTransformer()

    @property
    def target_event(self) -> Event:
        return Event.COMMUNITY_PARSED

    @property
    def platform_name(self) -> str:
        return "sinyi_community"

    def extract_source_id(self, url: str) -> Optional[str]:
        match = re.search(r'communityinfo/([A-Za-z0-9]+)', url)
        return match.group(1) if match else None

    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        使用 Container-based Locating 原則擷取社區資料。
        1. 先定位父容器 (Header Block, Address Block, Info Block)
        2. 再透過父容器物件往下搜尋所需元素
        """
        raw_data = {}

        # ── 1. Header Block: 取得社區名稱 ──
        header_block = tab.ele('css:h1[class*="community_object-text-name"]', timeout=5)
        if header_block:
            raw_data['name'] = header_block.text.strip()
            self.raw_elements['name'] = header_block

        # ── 2. Address Block: 取得社區地址 ──
        address = ""
        addr_block = tab.ele('css:div[class*="community_object-text-address"]', timeout=3)
        if addr_block:
            address = addr_block.text.strip()
            self.raw_elements['address'] = addr_block
        raw_data['address'] = address
        # ── 3. Image URL ──
        # 標示需指向有面積的容器 (div)，改用最外層的 carousel-frame 確保框住整張圖
        img_container = tab.ele('css:div[class^="community_object-carousel-frame__"]', timeout=3)
        if img_container:
            # 圖片網址藏在內層的 active 項目 img 中
            img_tag = img_container.ele('css:div.active img') or img_container.ele('tag:img')
            if img_tag:
                raw_data['image_url'] = img_tag.attr('src')
            self.raw_elements['image_url'] = img_container

        # ── 3. Basic Info Block: 取得社區規格資訊 ──
        specs = {}
        info_block = tab.ele(
            'css:div[class^="community_basic-info-area__"]',
            timeout=5
        )
        if info_block:
            # 在 info_block 容器內尋找 title-content 配對
            titles = info_block.eles('css:div[class*="basic-info-area-title"], div[class*="info-title"], span[class*="title"]')
            contents = info_block.eles('css:div[class*="basic-info-area-content"], div[class*="info-content"], span[class*="content"]')

            for i in range(min(len(titles), len(contents))):
                label = titles[i].text.strip()
                value = contents[i].text.strip()
                if label and value:
                    specs[label] = value
                    
                    container = titles[i].parent()
                    if label == '建設公司': self.raw_elements['builder'] = container
                    elif label == '戶數': self.raw_elements['total_households'] = container
                    elif label == '屋齡': self.raw_elements['age'] = container
                    elif label == '主要結構': self.raw_elements['building_structure'] = container

        raw_data['specs'] = specs

        # 補上 source_id 與 url
        raw_data['source_id'] = self.extract_source_id(url) or ""
        raw_data['url'] = url

        return raw_data

