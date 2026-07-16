import re
import time
import logging
from typing import Optional, Dict, Any

from ..base import BaseSpider
from ..factory import SpiderFactory
from ...engine.events import event_bus, Event
from ...engine.context import SpiderContext
from ...storage.interfaces import CheckStatus
from .navigator import YungchingCommunityNavigator
from .transformer import YungchingCommunityTransformer


@SpiderFactory.register("yungching_community")
class YungchingCommunitySpider(BaseSpider):
    """
    永慶房屋 - 社區資料爬蟲
    遵守 Container-based Locating 原則：先定位區塊，再往下尋找元素。
    """

    def __init__(self, config, **kwargs):
        super().__init__(config)
        self.navigator = YungchingCommunityNavigator()
        self.transformer = YungchingCommunityTransformer()

    @property
    def target_event(self) -> Event:
        return Event.COMMUNITY_PARSED

    @property
    def platform_name(self) -> str:
        return "yungching_community"

    def extract_source_id(self, url: str) -> Optional[str]:
        match = re.search(r'building/(\d+)', url)
        return match.group(1) if match else None

    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        使用 Container-based Locating 原則擷取社區資料。
        """
        raw_data = {}

        # ── 1. Header Block: 取得社區名稱 ──
        header_block = tab.ele('css:h1.buliding-name', timeout=5)
        if header_block:
            raw_data['name'] = header_block.text.strip()
            self.raw_elements['name'] = header_block

        # ── 2. Address Block: 取得社區地址 ──
        address = ""
        addr_block = tab.ele('css:h3.building-info-heading', timeout=3)
        if addr_block:
            address = addr_block.text.strip()
            self.raw_elements['address'] = addr_block
        raw_data['address'] = address
        
        # ── 3. Image URL ──
        img_ele = tab.ele('css:.building-photos img', timeout=3)
        if img_ele:
            raw_data['image_url'] = img_ele.attr('src')
            self.raw_elements['image_url'] = img_ele

        # ── 4. Info Block: 取得社區規格資訊 ──
        specs = {}
        info_block = tab.ele('css:ul.building-info-list', timeout=5)
        if info_block:
            # 在 info_block 容器內尋找 li 元素
            li_items = info_block.eles('tag:li')
            for li in li_items:
                text = li.text.strip().replace('\n', ' ')
                if '：' in text:
                    parts = text.split('：', 1)
                    if len(parts) == 2:
                        label = parts[0].strip().replace(' ', '') # 處理如 "主 結 構"
                        value = parts[1].strip()
                        if label and value:
                            specs[label] = value
                            
                            # 精確標示項目
                            if label == '建設公司': self.raw_elements['builder'] = li
                            elif label == '總戶數': self.raw_elements['total_households'] = li
                            elif label == '屋齡': self.raw_elements['age'] = li
                            elif label == '完工日期': self.raw_elements['completion_date'] = li
                            elif label == '主結構': self.raw_elements['building_structure'] = li

        raw_data['specs'] = specs
        raw_data['source_id'] = self.extract_source_id(url) or ""
        raw_data['url'] = url

        return raw_data
