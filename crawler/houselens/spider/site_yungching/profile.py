from ...spider.core.rules import FieldRule, MappingProfile
from ...spider.core.selectors import CssSelector, XPathSelector, LabelSiblingSelector, ParentSelector
from ...spider.core.processors import ExtractFloat, ParseLayout, ParseAge, RemoveSpaces, ExtractAfterString

def get_yungching_profile() -> MappingProfile:
    rules = [
        FieldRule(
            name="title",
            selector=CssSelector('.house-info .case-name'),
            processors=[RemoveSpaces()]
        ),
        FieldRule(
            name="total_price",
            selector=ParentSelector(XPathSelector('.//div[contains(@class, "house-info")]//*[contains(text(), "萬")]')),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="address",
            selector=CssSelector('.house-info .case-desc'),
            processors=[RemoveSpaces()]
        ),
        FieldRule(
            name="layout",
            selector=LabelSiblingSelector(["建物格局"], container_css=".item")
        ),
        FieldRule(
            name="building_ping",
            selector=LabelSiblingSelector(["建物坪數"], container_css=".item"),
            processors=[ExtractAfterString("建物坪數"), ExtractFloat()]
        ),
        FieldRule(
            name="main_building_ping",
            selector=LabelSiblingSelector(["主建物"], container_css=".item"),
            processors=[ExtractAfterString("主建物"), ExtractFloat()]
        ),
        FieldRule(
            name="shared_ping",
            selector=LabelSiblingSelector(["共同使用小計"], container_css=".item"),
            processors=[ExtractAfterString("共同使用小計"), ExtractFloat()]
        ),
        FieldRule(
            name="accessory_ping",
            selector=LabelSiblingSelector(["附屬建物小計"], container_css=".item"),
            processors=[ExtractAfterString("附屬建物小計"), ExtractFloat()]
        ),
        FieldRule(
            name="land_ping",
            selector=LabelSiblingSelector(["土地坪數"], container_css=".item"),
            processors=[ExtractAfterString("土地坪數"), ExtractFloat()]
        ),
        FieldRule(
            name="land_zoning",
            selector=LabelSiblingSelector(["土地使用分區"], container_css=".item"),
            processors=[ExtractAfterString("使用分區")]
        ),
        FieldRule(
            name="legal_usage",
            selector=LabelSiblingSelector(["謄本用途"], container_css=".item"),
            processors=[ExtractAfterString("謄本用途")]
        ),
        FieldRule(
            name="unit_price",
            selector=LabelSiblingSelector(["單價"], container_css=".item"),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="unit_price_fallback",
            selector=LabelSiblingSelector(["房貸"], container_css=".item"),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="raw_building_type",
            selector=LabelSiblingSelector(["型態"], container_css=".item"),
            processors=[ExtractAfterString("型態")]
        ),
        FieldRule(
            name="age",
            selector=LabelSiblingSelector(["屋齡"], container_css=".item"),
            processors=[ParseAge()]
        ),
        FieldRule(
            name="community_name",
            selector=LabelSiblingSelector(["社區"], container_css=".item"),
            processors=[ExtractAfterString("社區")]
        ),
        FieldRule(
            name="floor_info",
            selector=LabelSiblingSelector(["樓層"], container_css=".item")
        ),
        FieldRule(
            name="management_fee",
            selector=LabelSiblingSelector(["管理費"], container_css=".item")
        ),
        FieldRule(
            name="orientation",
            selector=LabelSiblingSelector(["朝向"], container_css=".item"),
            processors=[ExtractAfterString("朝向")]
        ),
        FieldRule(
            name="has_parking",
            selector=LabelSiblingSelector(["車位數量"], container_css=".item")
        ),
        FieldRule(
            name="parking_type",
            selector=LabelSiblingSelector(["車位"], container_css=".item") # Will extract later in transformer
        )
    ]
    return MappingProfile(rules=rules)
