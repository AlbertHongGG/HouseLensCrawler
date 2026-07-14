from ...spider.core.rules import ContainerRule, ListRule, FieldRule, KeyValueExtractionRule, MappingProfile
from ...spider.core.selectors import CssSelector, TextMatchSelector
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
                            selector=TextMatchSelector("單價", exact=False),
                            processors=[RegexProcessor(r'([\d.]+)萬/坪'), ExtractFloat()]
                        )
                    ]
                ),
                # 2.2 上方基本規格區塊 (格局、屋齡、坪數)
                ContainerRule(
                    name="top_basic_info_block",
                    selector=CssSelector(".info-floor-left, .detail-info-box-2"),
                    rules=[
                        ListRule(
                            name="top_specs_list",
                            item_selector=CssSelector(".info-floor-item, .info-floor-left-2"),
                            rules=[
                                KeyValueExtractionRule(
                                    key_selector=CssSelector(".info-floor-key, span:first-child"),
                                    value_selector=CssSelector(".info-floor-value, span:last-child"),
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
                # 2.3 地址與社區區塊
                ContainerRule(
                    name="location_block",
                    selector=CssSelector(".info-addr-content, .info-floor-right, .detail-info-box-3"),
                    rules=[
                        ListRule(
                            name="location_list",
                            item_selector=CssSelector(".info-addr-item, .info-floor-item"),
                            rules=[
                                KeyValueExtractionRule(
                                    key_selector=CssSelector(".info-addr-key, .info-floor-key"),
                                    value_selector=CssSelector(".info-addr-value, .info-floor-value"),
                                    key_mapping={
                                        "地址": "address",
                                        "社區": "community_name",
                                        "樓層": "floor_info"
                                    }
                                )
                            ]
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
        
        # 4. 細部資料區塊 (包含 現況:住宅 這種合併字串)
        ContainerRule(
            name="detail_introduction_area",
            selector=CssSelector(".detail-house-box, .detail-house-content, #new-vue-sale-detail-house"),
            rules=[
                FieldRule(
                    name="raw_building_type",
                    selector=TextMatchSelector("型態:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), RemoveSpaces()]
                ),
                FieldRule(
                    name="has_tenant",
                    selector=TextMatchSelector("帶租約:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), RemoveSpaces()]
                ),
                FieldRule(
                    name="legal_usage",
                    selector=TextMatchSelector("法定用途:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), RemoveSpaces()]
                ),
                FieldRule(
                    name="management_fee",
                    selector=TextMatchSelector("管理費:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), RemoveSpaces()]
                ),
                FieldRule(
                    name="parking_info",
                    selector=TextMatchSelector("車位:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), RemoveSpaces()]
                ),
                FieldRule(
                    name="main_building_ping",
                    selector=TextMatchSelector("主建物:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), ExtractFloat()]
                ),
                FieldRule(
                    name="accessory_ping",
                    selector=TextMatchSelector("附屬建物:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), ExtractFloat()]
                ),
                FieldRule(
                    name="shared_ping",
                    selector=TextMatchSelector("共用部分:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), ExtractFloat()]
                ),
                FieldRule(
                    name="land_ping",
                    selector=TextMatchSelector("土地坪數:", exact=False),
                    processors=[SplitProcessor(delimiter=':'), SplitProcessor(delimiter='：'), ExtractFloat()]
                )
            ]
        )
    ]
    
    return MappingProfile(rules=rules)
