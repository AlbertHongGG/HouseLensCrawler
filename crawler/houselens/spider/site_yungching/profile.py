from ...spider.core.rules import ContainerRule, ListRule, FieldRule, KeyValueExtractionRule, BlockKeyValueRule, MappingProfile
from ...spider.core.selectors import CssSelector, XPathSelector, MultipleSelector
from ...spider.core.processors import ExtractFloat, ParseAge, RemoveSpaces
from ...spider.core.post_processors import CalculateIndoorPingProcessor

def get_yungching_profile() -> MappingProfile:
    rules = [
        # 1. House Info Block (Top Area)
        ContainerRule(
            name="house_info_block",
            selector=CssSelector('div.house-info, .m-house-detail-header, .house-info-name'),
            rules=[
                FieldRule(
                    name="title",
                    selector=CssSelector('.case-name, h1, .title'),
                    processors=[RemoveSpaces()]
                ),
                FieldRule(
                    name="total_price",
                    # 精準抓取折扣後的價格，避免抓到劃掉的原價
                    selector=CssSelector('.price-wrapper .price, .price-num, .price-info'),
                    processors=[ExtractFloat()]
                ),
                FieldRule(
                    name="address",
                    selector=MultipleSelector([
                        CssSelector('.address-text'),
                        CssSelector('.address, .house-address')
                    ]),
                    processors=[RemoveSpaces()]
                ),
                FieldRule(
                    name="community_name",
                    selector=CssSelector('a.community, .community-name'),
                    processors=[RemoveSpaces()]
                )
            ]
        ),
        
        # 2. Image Gallery Block
        ContainerRule(
            name="gallery_block",
            selector=CssSelector('.house-album, .album-handlers-swiper, .yc-ng-album, .slick-track, .house-photo'),
            rules=[
                FieldRule(
                    name="image_urls",
                    selector=CssSelector('img'),
                    extract_attr='src',
                    is_list=True
                )
            ]
        ),
        
        # 3. Basic Detail Block (Strictly scoped)
        ContainerRule(
            name="basic_info_block",
            # Strictly limit to the detail blocks to avoid matching `.item` globally
            selector=CssSelector('.detail-block.basic, .m-house-detail-list, .detail-list, .house-detail-info'),
            rules=[
                ListRule(
                    name="basic_info_list",
                    item_selector=CssSelector('.detail-row, .item, li'),
                    rules=[
                        BlockKeyValueRule(
                            key_mapping={
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
                                "車位": "parking_type"
                            },
                            value_processors={
                                "building_ping": [ExtractFloat()],
                                "main_building_ping": [ExtractFloat()],
                                "shared_ping": [ExtractFloat()],
                                "accessory_ping": [ExtractFloat()],
                                "land_ping": [ExtractFloat()],
                                "unit_price": [ExtractFloat()],
                                "unit_price_fallback": [ExtractFloat()],
                                "age": [ParseAge()]
                            }
                        )
                    ]
                )
            ]
        )
    ]


    return MappingProfile(rules=rules, post_processors=[CalculateIndoorPingProcessor()])
