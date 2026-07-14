from ...spider.core.rules import FieldRule, BlockRule, MappingProfile, KeyValueRule
from ...spider.core.selectors import CssSelector, XPathSelector, LabelSiblingSelector
from ...spider.core.processors import ExtractFloat, ParseLayout, ParseAge, RemoveSpaces, ExtractAfterString

def get_591_profile() -> MappingProfile:
    blocks = [
        # 1. 標題區塊
        BlockRule(
            name="title_block",
            container_selector=CssSelector(".detail-title-container, #detail-title-container-template"),
            fields=[
                FieldRule(
                    name="title",
                    selector=XPathSelector('.//h1', timeout=0),
                    processors=[RemoveSpaces()]
                )
            ]
        ),
        
        # 2. 核心資訊區塊
        BlockRule(
            name="info_block",
            container_selector=CssSelector("#new-vue-sale-detail-info, .detail-info, .info-box"),
            fields=[
                FieldRule(
                    name="total_price",
                    selector=XPathSelector('.//*[contains(@class, "info-box-price-2")]//*[contains(@class, "price")]', timeout=0),
                    processors=[ExtractFloat()]
                ),
                FieldRule(
                    name="unit_price",
                    selector=XPathSelector('.//*[contains(@class, "info-box-price-2")]//*[contains(text(), "萬/坪")]', timeout=0),
                    processors=[ExtractFloat()]
                ),
                FieldRule(
                    name="building_ping",
                    selector=LabelSiblingSelector(["權狀坪數"], container_css=".info-floor-left-2"),
                    processors=[ExtractFloat()]
                ),
                FieldRule(
                    name="layout",
                    selector=LabelSiblingSelector(["格局"], container_css=".info-floor-left-2")
                ),
                FieldRule(
                    name="age",
                    selector=LabelSiblingSelector(["屋齡"], container_css=".info-floor-left-2"),
                    processors=[ParseAge()]
                ),
                FieldRule(
                    name="floor_info",
                    selector=LabelSiblingSelector(["樓層"], container_css=".info-addr-content")
                ),
                FieldRule(
                    name="address",
                    selector=LabelSiblingSelector(["地址"], container_css=".info-addr-content")
                ),
                FieldRule(
                    name="community_name",
                    selector=LabelSiblingSelector(["社區"], container_css=".info-addr-content")
                ),
                FieldRule(
                    name="orientation",
                    selector=LabelSiblingSelector(["朝向"], container_css=".info-addr-content")
                )
            ]
        )
    ]
    
    # 圖片等其他不屬於特定大區塊的資料，可以放在 global rules
    rules = [
        FieldRule(
            name="image_urls",
            selector=CssSelector('.img-box img, #j_photo_play img, #img_list img'),
            extract_attr='src',
            is_list=True
        )
    ]
    
    # 3. 房屋資料區塊與 4. 坪數說明區塊，透過 KeyValueRule 處理防爬標籤
    kv_rules = [
        KeyValueRule(
            container_selector=CssSelector(".detail-house-item, .house-info-item"),
            key_selector=CssSelector(".detail-house-key, .house-info-name"),
            value_selector=CssSelector(".detail-house-value, .house-info-value"),
            key_mapping={
                "型態": "raw_building_type",
                "管理費": "management_fee",
                "帶租約": "has_tenant",
                "法定用途": "legal_usage",
                "車位": "parking_info"
            }
        ),
        KeyValueRule(
            container_selector=CssSelector(".detail-house-item, .house-info-item"),
            key_selector=CssSelector(".detail-house-key, .house-info-name"),
            value_selector=CssSelector(".detail-house-value, .house-info-value"),
            key_mapping={
                "主建物": "main_building_ping",
                "附屬建物": "accessory_ping",
                "共用部分": "shared_ping",
                "土地坪數": "land_ping",
                "土地持分坪數": "land_ping"
            },
            value_processors={
                "main_building_ping": [ExtractFloat()],
                "accessory_ping": [ExtractFloat()],
                "shared_ping": [ExtractFloat()],
                "land_ping": [ExtractFloat()]
            }
        )
    ]
    
    return MappingProfile(rules=rules, blocks=blocks, key_value_rules=kv_rules)
