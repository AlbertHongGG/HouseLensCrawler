import time
import logging
import re
from typing import Optional, Dict, Any
from ..base import BaseSpider
from ...engine.events import Event
from .navigator import Spider591Navigator
from .transformer import Spider591Transformer
from ..factory import SpiderFactory

@SpiderFactory.register("591")
class Spider591(BaseSpider):
    def __init__(self, config=None, **kwargs):
        super().__init__(config, **kwargs)
        self.navigator = Spider591Navigator()
        self.transformer = Spider591Transformer()

    @property
    def target_event(self) -> Event:
        return Event.ITEM_PARSED

    @property
    def platform_name(self) -> str:
        return "591"

    def extract_source_id(self, url: str) -> Optional[str]:
        try:
            match = re.search(r'detail/\d+/(\d+)\.html', url)
            return match.group(1) if match else None
        except Exception:
            return None

    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        Naked DrissionPage implementation using strict container boundaries.
        Translates exactly the locators from the old profile.py.
        """
        raw_data = {}

        # 1. Title Block
        title_block = tab.ele('css:.detail-title-container, #detail-title-container-template, .detail-title', timeout=3)
        if title_block:
            title_ele = title_block.ele('css:.detail-title-text, #title-new, h1', timeout=0)
            if title_ele:
                raw_data['title'] = title_ele.text
                self.raw_elements['title'] = title_ele

        # 2. Main Info Block
        main_info_area = tab.ele('css:#new-vue-sale-detail-info, .detail-info-box-1, .detail-info-right', timeout=2)
        if main_info_area:
            # 2.1 Price
            price_block = main_info_area.ele('css:.info-box-price-2, .price-wrapper', timeout=0)
            if price_block:
                total_price_ele = price_block.ele('css:.info-price-text, .info-price-num-2, .price-num', timeout=0)
                if total_price_ele:
                    raw_data['total_price'] = total_price_ele.text
                    self.raw_elements['total_price'] = total_price_ele
                
                unit_price_ele = price_block.ele('css:.info-price-per', timeout=0)
                if unit_price_ele:
                    raw_data['unit_price'] = unit_price_ele.text
                    self.raw_elements['unit_price'] = unit_price_ele

            # 2.2 Top Basic Info (Specs)
            top_basic_block = main_info_area.ele('css:.info-floor-left, .detail-info-box-2, .info-box-floor', timeout=0)
            if top_basic_block:
                top_items = top_basic_block.eles('css:.info-floor-item, .info-floor-left-2, .info-floor-left > div, .info-box-floor > div')
                key_mapping = {
                    "權狀坪數": "building_ping",
                    "格局": "layout",
                    "屋齡": "age"
                }
                for item in top_items:
                    text = item.text.replace(' ', '').replace('\n', '').strip() if item.text else ""
                    for mapped_key_name, target_field in key_mapping.items():
                        if mapped_key_name in text:
                            raw_value = text.replace(mapped_key_name, '').replace(':', '').replace('：', '')
                            raw_data[target_field] = raw_value
                            self.raw_elements[target_field] = item

            # 2.3 Location List
            location_items = main_info_area.eles('css:.info-addr-content, .info-floor-item')
            loc_key_mapping = {
                "地址": "address",
                "社區": "community_name",
                "樓層": "floor_info",
                "朝向": "orientation"
            }
            for item in location_items:
                text = item.text.replace(' ', '').replace('\n', '').strip() if item.text else ""
                for mapped_key_name, target_field in loc_key_mapping.items():
                    if mapped_key_name in text:
                        raw_value = text.replace(mapped_key_name, '').replace(':', '').replace('：', '')
                        raw_data[target_field] = raw_value
                        self.raw_elements[target_field] = item

        # 3. Gallery Block
        gallery_block = tab.ele('css:.img-box, #j_photo_play, #img_list', timeout=1)
        if gallery_block:
            imgs = gallery_block.eles('tag:img')
            g_urls = [img.attr('src') for img in imgs if img.attr('src')]
            if g_urls:
                raw_data['image_urls'] = g_urls
                self.raw_elements['image_urls'] = gallery_block

        # 4. Detail House Info Block
        detail_house_block = tab.ele('css:.detail-house, #new-vue-sale-detail-house, .house-info-wrap, section.detail-house', timeout=2)
        if detail_house_block:
            house_items = detail_house_block.eles('css:.detail-house-item, .house-info-item, .detail-house-content > div')
            house_key_mapping = {
                "型態": "raw_building_type",
                "帶租約": "has_tenant",
                "法定用途": "legal_usage",
                "管理費": "management_fee",
                "車位": "parking_info",
                "主建物": "main_building_ping",
                "附屬建物": "accessory_ping",
                "共用部分": "shared_ping",
                "土地坪數": "land_ping",
                "土地持分坪數": "land_ping",
                "土地(持分)坪數": "land_ping",
                "土地（持分）坪數": "land_ping"
            }
            for item in house_items:
                text = item.text.replace(' ', '').replace('\n', '').strip() if item.text else ""
                for mapped_key_name, target_field in house_key_mapping.items():
                    if mapped_key_name in text:
                        raw_value = text.replace(mapped_key_name, '').replace(':', '').replace('：', '')
                        raw_data[target_field] = raw_value
                        self.raw_elements[target_field] = item

        return raw_data
