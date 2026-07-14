from ...spider.core.rules import FieldRule, MappingProfile
from ...spider.core.selectors import CssSelector, XPathSelector, LabelSiblingSelector
from ...spider.core.processors import ExtractFloat, ParseLayout, ParseAge, RemoveSpaces, ExtractAfterString
from ...spider.core.processors import BaseProcessor
from typing import Any, Optional, Dict
import re

class SinyiParkingProcessor(BaseProcessor):
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        if not value or not isinstance(value, str):
            return ""
        # 移除收合、更多等按鈕文字
        val = value.replace('收合', '').replace('更多', '').replace('車位', '').strip()
        return val

def get_sinyi_profile() -> MappingProfile:
    rules = [
        FieldRule(
            name="title",
            selector=XPathSelector('//span[contains(@class, "buy-content-title-name")]', timeout=10),
            processors=[RemoveSpaces()]
        ),
        FieldRule(
            name="total_price",
            selector=XPathSelector('//div[contains(@class, "buy-content-title-total-price")]', timeout=2),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="address",
            selector=XPathSelector('//span[contains(@class, "buy-content-title-address")]', timeout=2),
            processors=[RemoveSpaces()]
        ),
        # Basic Block Fields
        FieldRule(
            name="building_ping",
            selector=LabelSiblingSelector(["建坪"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="unit_price",
            selector=LabelSiblingSelector(["建坪單價"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="main_building_ping",
            selector=LabelSiblingSelector(["主建物", "主+附"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="shared_ping",
            selector=LabelSiblingSelector(["共有部份"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="accessory_ping",
            selector=LabelSiblingSelector(["附屬建物"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="land_ping",
            selector=LabelSiblingSelector(["地坪"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="balcony_ping",
            selector=LabelSiblingSelector(["陽台"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="rain_cover_ping",
            selector=LabelSiblingSelector(["雨遮"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="raw_building_type",
            selector=LabelSiblingSelector(["類型"]),
            processors=[ExtractAfterString("類型")]
        ),
        FieldRule(
            name="layout",
            selector=LabelSiblingSelector(["格局"]),
            processors=[ExtractAfterString("格局")]
        ),
        FieldRule(
            name="age",
            selector=LabelSiblingSelector(["屋齡"]),
            processors=[ParseAge()]
        ),
        FieldRule(
            name="floor_info",
            selector=LabelSiblingSelector(["樓層"]),
            processors=[ExtractAfterString("樓層")]
        ),
        FieldRule(
            name="parking_ping",
            selector=LabelSiblingSelector(["停車空間"]),
            processors=[ExtractFloat()]
        ),
        FieldRule(
            name="parking_type",
            selector=LabelSiblingSelector(["車位"]),
            processors=[SinyiParkingProcessor()]
        ),
        FieldRule(
            name="management_fee",
            selector=LabelSiblingSelector(["警衛管理", "管理費"]),
            processors=[ExtractAfterString("管理")] # Extracts after 警衛管理 or 管理費
        ),
        FieldRule(
            name="orientation",
            selector=LabelSiblingSelector(["建物朝向", "落地窗朝向", "朝向"]),
            processors=[ExtractAfterString("朝向")]
        )
    ]
    return MappingProfile(rules=rules)
