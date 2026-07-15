import time
import logging
from typing import Optional, Dict, Any
from ..base import BaseSpider
from .navigator import SpiderYungchingNavigator
from .transformer import YungchingTransformer
from ..factory import SpiderFactory

@SpiderFactory.register("yungching")
class YungchingSpider(BaseSpider):
    def __init__(self, config):
        super().__init__(config)
        self.navigator = SpiderYungchingNavigator()
        self.transformer = YungchingTransformer()

    @property
    def platform_name(self) -> str:
        return "yungching"

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

        # 1. House Info Block (Top Area)
        house_info_block = tab.ele('css:div.house-info, .m-house-detail-header, .house-info-name', timeout=3)
        if house_info_block:
            title_ele = house_info_block.ele('css:.case-name, h1, .title', timeout=0)
            if title_ele: raw_data['title'] = title_ele.text

            price_ele = house_info_block.ele('css:.price-wrapper .price, .price-num, .price-info', timeout=0)
            if price_ele: raw_data['total_price'] = price_ele.text

            addr_ele = house_info_block.ele('css:.address-text', timeout=0) or house_info_block.ele('css:.address, .house-address', timeout=0)
            if addr_ele: raw_data['address'] = addr_ele.text

            community_ele = house_info_block.ele('css:a.community, .community-name', timeout=0)
            if community_ele: raw_data['community_name'] = community_ele.text

        # 2. Image Gallery Block
        gallery_block = tab.ele('css:.house-album, .album-handlers-swiper, .yc-ng-album, .slick-track, .house-photo', timeout=1)
        if gallery_block:
            imgs = gallery_block.eles('tag:img')
            raw_data['image_urls'] = [img.attr('src') for img in imgs if img.attr('src')]

        # 3. Basic Detail Block (Strictly scoped)
        basic_info_block = tab.ele('css:.detail-block.basic, .house-detail-info:not(.detail-list)', timeout=2)
        if basic_info_block:
            items = basic_info_block.eles('css:.item, li')
            
            key_mapping = {
                "建物格局": "layout",
                "建物坪數": "building_ping",
                "主建物": "main_building_ping",
                "共同使用小計": "shared_ping",
                "附屬建物小計": "accessory_ping",
                "土地坪數": "land_ping",
                "土地使用分區": "land_zoning",
                "謄本用途": "legal_usage",
                "單價": "unit_price",
                "房貸": "unit_price_fallback",
                "型態": "raw_building_type",
                "屋齡": "age",
                "樓層": "floor_info",
                "管理費": "management_fee",
                "朝向": "orientation",
                "車位數量": "has_parking",
                "・車位": "parking_type"
            }

            for item in items:
                k_ele = item.ele('css:.item-title', timeout=0)
                v_ele = item.ele('css:.item-detail', timeout=0)
                if k_ele and v_ele:
                    key_text = k_ele.text.replace(" ", "").replace("\n", "").replace("\u3000", "").replace("\t", "")
                    val_text = v_ele.text.strip()
                    
                    for mapped_key_name, target_field in key_mapping.items():
                        if mapped_key_name in key_text:
                            raw_data[target_field] = val_text
                            
                            if target_field == "parking_type" and '\n' in val_text:
                                raw_data[target_field] = val_text.split('\n')[0]
                            break

        return raw_data
