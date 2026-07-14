from ...spider.core.rules import FieldRule, BlockRule, MappingProfile
from ...spider.core.selectors import CssSelector, XPathSelector, LabelSiblingSelector
from ...spider.core.processors import ExtractFloat, ParseLayout, ParseAge, RemoveSpaces, ExtractAfterString

def get_591_profile() -> MappingProfile:
    rules = [
        FieldRule(
            name="title",
            selector=XPathSelector('.//h1', timeout=0),
            processors=[RemoveSpaces()]
        ),
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
        ),
        FieldRule(
            name="raw_building_type",
            selector=LabelSiblingSelector(["型態"], container_css=".detail-house-item, .house-info-item")
        ),
        FieldRule(
            name="management_fee",
            selector=LabelSiblingSelector(["管理費"], container_css=".detail-house-item, .house-info-item")
        ),
        FieldRule(
            name="has_tenant",
            selector=LabelSiblingSelector(["帶租約"], container_css=".detail-house-item, .house-info-item")
        ),
        FieldRule(
            name="legal_usage",
            selector=LabelSiblingSelector(["法定用途"], container_css=".detail-house-item, .house-info-item")
        ),
        FieldRule(
            name="parking_info",
            selector=LabelSiblingSelector(["車位"], container_css=".detail-house-item, .house-info-item")
        ),
        FieldRule(
            name="main_building_ping",
            selector=LabelSiblingSelector(["主建物"], container_css=".detail-house-item, .house-info-item"),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="accessory_ping",
            selector=LabelSiblingSelector(["附屬建物"], container_css=".detail-house-item, .house-info-item"),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="shared_ping",
            selector=LabelSiblingSelector(["共用部分"], container_css=".detail-house-item, .house-info-item"),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="land_ping",
            selector=LabelSiblingSelector(["土地坪數", "土地(持分)坪數", "土地（持分）坪數"], container_css=".detail-house-item, .house-info-item"),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="image_urls",
            selector=CssSelector('.img-box img, #j_photo_play img, #img_list img'),
            extract_attr='src',
            is_list=True
        )
    ]
    return MappingProfile(rules=rules)
