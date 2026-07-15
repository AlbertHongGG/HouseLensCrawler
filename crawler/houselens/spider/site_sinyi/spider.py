import time
import logging
import re
from typing import Optional, Dict, Any
from ..base import BaseSpider
from .navigator import SinyiNavigator
from .transformer import SinyiTransformer
from ..factory import SpiderFactory

@SpiderFactory.register("sinyi")
class SinyiSpider(BaseSpider):
    def __init__(self, config):
        super().__init__(config)
        self.navigator = SinyiNavigator()
        self.transformer = SinyiTransformer()

    @property
    def platform_name(self) -> str:
        return "sinyi"

    def extract_source_id(self, url: str) -> Optional[str]:
        try:
            return url.split('/')[-1].split('?')[0]
        except Exception:
            return None

    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        Naked DrissionPage implementation using strict container boundaries.
        Translates exactly the locators from the old profile.py.
        """
        raw_data = {}

        # 1. Header Information Block
        header_block = tab.ele('css:div[class*="buy_buy-content-top-bar-title"], .buy-content-title, .buy-title, .m-house-detail-header', timeout=3)
        if not header_block:
            header_block = tab.ele('css:body', timeout=0)

        if header_block:
            title_ele = header_block.ele('css:.buy-content-title-name, .title, h1', timeout=0)
            if title_ele: raw_data['title'] = title_ele.text

            price_ele = header_block.ele('css:.buy-content-title-total-price, div[class*="buy_buy-content-title-price-first"], .price', timeout=0)
            if price_ele: raw_data['total_price'] = price_ele.text

            addr_ele = header_block.ele('xpath://div[contains(text(), "地址")] | //span[contains(text(), "地址")] | //*[contains(@class, "address")]', timeout=0)
            if not addr_ele:
                addr_ele = header_block.ele('css:div[class*="Address"]', timeout=0)
            if addr_ele: raw_data['address'] = addr_ele.text

            community_ele = header_block.ele('css:a[href*="/communitylist/communityinfo/"], div[class*="community-btn"]', timeout=0)
            if community_ele: raw_data['community_name'] = community_ele.text
            
            # thumbnail images
            thumb_imgs = header_block.eles('css:div[class*="thumbnail"] img')
            if thumb_imgs:
                raw_data['image_urls'] = [img.attr('src') for img in thumb_imgs if img.attr('src')]

        # 2. Image Gallery Block (overwrite image_urls if found)
        gallery_block = tab.ele('css:div[class*="buy_buy-content-carousel"], .buy-buy-carousel, .carousel_carousel-thumbnail, .slick-slider', timeout=1)
        if gallery_block:
            imgs = gallery_block.eles('tag:img')
            g_urls = [img.attr('src') for img in imgs if img.attr('src')]
            if g_urls:
                if 'image_urls' in raw_data:
                    raw_data['image_urls'].extend(g_urls)
                else:
                    raw_data['image_urls'] = g_urls

        # 3. Basic Information Block
        basic_info_block = tab.ele('css:div[class*="buy_buy-content-basic"], #basic-data, .buy-content-basic, .basic-info-content', timeout=2)
        if basic_info_block:
            items = basic_info_block.eles('css:div[class*="buy_buy-content-body-grid"] > div, .item, .buy-content-basic-cell, li, div[class*="buy_buy-content-basic"]')
            
            key_mapping = {
                "建坪單價": "unit_price",
                "建坪": "building_ping",
                "主+附": "indoor_ping",
                "主+陽": "indoor_ping",
                "主建物": "main_building_ping",
                "共有部份": "shared_ping",
                "附屬建物": "accessory_ping",
                "地坪": "land_ping",
                "陽台": "balcony_ping",
                "雨遮": "rain_cover_ping",
                "防空避難室兼停車場": "parking_ping",
                "防空避難室": "parking_ping",
                "類型": "raw_building_type",
                "停車空間": "parking_ping",
                "管理費": "management_fee",
                "車位": "parking_type",
                "建物朝向": "orientation",
                "格局": "layout",
                "屋齡": "age",
                "樓層": "floor_info"
            }

            for item in items:
                raw_html = item.html
                if not raw_html:
                    continue
                
                text = re.sub(r'<[^>]+>', '', raw_html)
                text = text.replace(' ', '').replace('\n', '').strip()
                
                for mapped_key_name, target_field in key_mapping.items():
                    if mapped_key_name in text:
                        raw_value = text.replace(mapped_key_name, '')
                        raw_value = raw_value.replace(':', '').replace('：', '')
                        raw_data[target_field] = raw_value

        return raw_data
