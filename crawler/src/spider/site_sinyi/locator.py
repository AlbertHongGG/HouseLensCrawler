from typing import Dict, Any, List

from ..interfaces import ILocator

class SinyiLocator(ILocator):
    """
    Handles DOM element location for Sinyi.
    Returns DrissionPage elements which can be highlighted or parsed later.
    """

    def locate_detail(self, tab) -> Dict[str, Any]:
        """Locates specific data fields on the detail page."""
        elements: Dict[str, Any] = {}
        
        # 標題
        tab.wait.eles_loaded('xpath://span[contains(@class, "buy-content-title-name")]', timeout=10)
        title_ele = tab.ele('xpath://span[contains(@class, "buy-content-title-name")]')
        if title_ele:
            elements['title'] = title_ele
            
        # 總價
        price_ele = tab.ele('xpath://div[contains(@class, "buy-content-title-total-price")]', timeout=2)
        if price_ele:
            elements['price'] = price_ele
            
        # 地址
        addr_ele = tab.ele('xpath://span[contains(@class, "buy-content-title-address")]', timeout=2)
        if addr_ele:
            elements['address'] = addr_ele

        # 基本資料區塊
        tab.wait.eles_loaded('xpath://div[contains(@class, "buy_buy-content-basic")]', timeout=10)
        basic_block = tab.ele('xpath://div[contains(@class, "buy_buy-content-basic")]')
        
        if basic_block:
            # 為了讓 Visualizer 可以精準 highlight 每個項目，我們透過 text 尋找對應的父容器
            labels = {
                "建坪單價": "unit_price",
                "建坪": "building_ping",
                "主建物": "main_building_ping",
                "共有部份": "shared_ping",
                "附屬建物": "accessory_ping",
                "地坪": "land_ping",
                "陽台": "balcony_ping",
                "雨遮": "rain_cover_ping",
                "類型": "building_type",
                "格局": "layout",
                "屋齡": "age",
                "樓層": "floor",
                "管理費": "management_fee",
                "朝向": "orientation",
                "車位": "parking"
            }
            
            for label_text, key in labels.items():
                label_ele = basic_block.ele(f'text:{label_text}', timeout=0.1)
                if label_ele:
                    # 在信義房屋的 DOM 中，標題與數值通常被包裝在同一個 div 裡面
                    # 所以我們往上找 1 或 2 層，直到找到包含換行的那個區塊
                    parent = label_ele.parent()
                    
                    # 避免抓到最外層的 basic_block 導致畫了滿版的框
                    if parent and parent != basic_block:
                        # 檢查如果父元素的文本長度過長 (包含了其他項目)，就只用自己那一層
                        if len(parent.text) < 50:
                            elements[key] = parent
                        else:
                            elements[key] = label_ele
            
            # 保留 basic_block 供 Parser 繼續分析所有文字 (加底線以防 Visualizer 畫框)
            elements['_basic_block'] = basic_block
            
        return elements
