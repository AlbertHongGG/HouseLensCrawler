from ...spider.core.rules import ContainerRule, ListRule, FieldRule, KeyValueExtractionRule, BlockKeyValueRule, MappingProfile
from ...spider.core.selectors import CssSelector, TextMatchSelector, XPathSelector
from ...spider.core.processors import ExtractFloat, ParseAge, RemoveSpaces, SplitProcessor, RegexProcessor

def get_591_profile() -> MappingProfile:
    rules = [
        # 1. 標題區塊
        ContainerRule(
            name="title_block",
            selector=CssSelector(".detail-title-container, #detail-title-container-template, .detail-title"),
            rules=[
                FieldRule(
                    name="title",
                    selector=CssSelector(".detail-title-text, #title-new, h1"),
                    processors=[RemoveSpaces()]
                )
            ]
        ),
        
        # 2. 核心資訊區塊 (包含價格、格局、地址等)
        ContainerRule(
            name="main_info_area",
            selector=CssSelector("#new-vue-sale-detail-info, .detail-info-box-1, .detail-info-right"),
            rules=[
                # 2.1 價格區塊
                ContainerRule(
                    name="price_block",
                    selector=CssSelector(".info-box-price-2, .price-wrapper"),
                    rules=[
                        FieldRule(
                            name="total_price",
                            selector=CssSelector(".info-price-text, .info-price-num-2, .price-num"),
                            processors=[ExtractFloat()]
                        ),
                        FieldRule(
                            name="unit_price",
                            selector=CssSelector(".info-price-per"),
                            processors=[RegexProcessor(r'([\d.]+)萬/坪'), ExtractFloat()]
                        )
                    ]
                ),
                # 2.2 上方基本規格區塊 (格局、屋齡、坪數)
                ContainerRule(
                    name="top_basic_info_block",
                    selector=CssSelector(".info-floor-left, .detail-info-box-2, .info-box-floor"),
                    rules=[
                        ListRule(
                            name="top_specs_list",
                            item_selector=CssSelector(".info-floor-item, .info-floor-left-2, .info-floor-left > div, .info-box-floor > div"),
                            rules=[
                                BlockKeyValueRule(
                                    key_mapping={
                                        "權狀坪數": "building_ping",
                                        "格局": "layout",
                                        "屋齡": "age"
                                    },
                                    value_processors={
                                        "building_ping": [ExtractFloat()],
                                        "age": [ParseAge()]
                                    }
                                )
                            ]
                        )
                    ]
                ),
                # 2.3 地址與社區區塊 (直接在 main_info_area 範圍內搜尋)
                ListRule(
                    name="location_list",
                    item_selector=CssSelector(".info-addr-content, .info-floor-item"),
                    rules=[
                        BlockKeyValueRule(
                            key_mapping={
                                "地址": "address",
                                "社區": "community_name",
                                "樓層": "floor_info",
                                "朝向": "orientation"
                            }
                        )
                    ]
                )
            ]
        ),
        
        # 3. 圖片區塊
        ContainerRule(
            name="gallery_block",
            selector=CssSelector('.img-box, #j_photo_play, #img_list'),
            rules=[
                FieldRule(
                    name="image_urls",
                    selector=CssSelector('img'),
                    extract_attr='src',
                    is_list=True
                )
            ]
        ),
        
        # 4. 房屋資料與坪數說明區塊 (整合)
        ContainerRule(
            name="detail_house_info_block",
            selector=CssSelector('.detail-house, #new-vue-sale-detail-house, .house-info-wrap, section.detail-house'),
            rules=[
                ListRule(
                    name="house_info_list",
                    item_selector=CssSelector(".detail-house-item, .house-info-item, .detail-house-content > div"),
                    rules=[
                        BlockKeyValueRule(
                            key_mapping={
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
                            },
                            value_processors={
                                "main_building_ping": [ExtractFloat()],
                                "accessory_ping": [ExtractFloat()],
                                "shared_ping": [ExtractFloat()],
                                "land_ping": [ExtractFloat()]
                            }
                        )
                    ]
                )
            ]
        )
    ]
    
    return MappingProfile(rules=rules)
