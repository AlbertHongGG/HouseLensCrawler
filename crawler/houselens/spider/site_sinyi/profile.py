from ...spider.core.rules import ContainerRule, ListRule, FieldRule, KeyValueExtractionRule, MappingProfile
from ...spider.core.selectors import CssSelector, XPathSelector
from ...spider.core.processors import ExtractFloat, ParseAge, RemoveSpaces, BaseProcessor
from typing import Any, Optional, Dict

class SinyiParkingProcessor(BaseProcessor):
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        if not value or not isinstance(value, str):
            return ""
        val = value.replace('收合', '').replace('更多', '').replace('車位', '').strip()
        return val

def get_sinyi_profile() -> MappingProfile:
    rules = [
        # 1. Header Information Block (Title, Price, Address)
        ContainerRule(
            name="header_block",
            selector=CssSelector(".buy-content-title, .buy-title, .m-house-detail-header"),
            rules=[
                FieldRule(
                    name="title",
                    selector=CssSelector(".buy-content-title-name, h1, .title"),
                    processors=[RemoveSpaces()]
                ),
                FieldRule(
                    name="total_price",
                    selector=CssSelector(".buy-content-title-total-price, .price"),
                    processors=[ExtractFloat()]
                ),
                FieldRule(
                    name="address",
                    selector=CssSelector(".buy-content-title-address, .address"),
                    processors=[RemoveSpaces()]
                )
            ]
        ),
        
        # 2. Image Gallery Block
        ContainerRule(
            name="gallery_block",
            selector=CssSelector(".buy-buy-carousel, .carousel_carousel-thumbnail, .slick-slider"),
            rules=[
                FieldRule(
                    name="image_urls",
                    selector=CssSelector("img"),
                    extract_attr='src',
                    is_list=True
                )
            ]
        ),
        
        # 3. Basic Information Block (Strictly limited to the table to avoid catching header specs)
        ContainerRule(
            name="basic_info_block",
            # We strictly target #basic-data or specific basic table classes.
            selector=CssSelector("#basic-data, .buy-content-basic, .basic-info-content"),
            rules=[
                ListRule(
                    name="basic_info_list",
                    item_selector=CssSelector(".item, .buy-content-basic-cell, li"),
                    rules=[
                        KeyValueExtractionRule(
                            key_selector=CssSelector("span:first-child, .title, label"),
                            value_selector=CssSelector("span:last-child, .value, .content"),
                            key_mapping={
                                "建坪單價": "unit_price",
                                "建坪": "building_ping",
                                "主建物": "main_building_ping",
                                "主+附": "main_building_ping",
                                "共有部份": "shared_ping",
                                "附屬建物": "accessory_ping",
                                "地坪": "land_ping",
                                "陽台": "balcony_ping",
                                "雨遮": "rain_cover_ping",
                                "類型": "raw_building_type",
                                "停車空間": "parking_ping",
                                "車位": "parking_type",
                                "警衛管理": "management_fee",
                                "管理費": "management_fee",
                                "建物朝向": "orientation",
                                "落地窗朝向": "orientation",
                                "朝向": "orientation",
                                "格局": "layout",
                                "屋齡": "age",
                                "樓層": "floor_info"
                            },
                            value_processors={
                                "unit_price": [ExtractFloat()],
                                "building_ping": [ExtractFloat()],
                                "main_building_ping": [ExtractFloat()],
                                "shared_ping": [ExtractFloat()],
                                "accessory_ping": [ExtractFloat()],
                                "land_ping": [ExtractFloat()],
                                "balcony_ping": [ExtractFloat()],
                                "rain_cover_ping": [ExtractFloat()],
                                "parking_ping": [ExtractFloat()],
                                "parking_type": [SinyiParkingProcessor()],
                                "age": [ParseAge()]
                            }
                        )
                    ]
                )
            ]
        )
    ]
    
    return MappingProfile(rules=rules)
