from typing import Dict, Any, List

class SinyiLocator:
    """
    Handles DOM element location for Sinyi.
    Returns DrissionPage elements which can be highlighted or parsed later.
    """
    
    def locate_list_items(self, page) -> List[Any]:
        """Locates all property cards on the list page."""
        page.wait.eles_loaded('xpath://div[contains(@id, "buyHouseCard_")]', timeout=10)
        return page.eles('xpath://div[contains(@id, "buyHouseCard_")]')

    def locate_detail(self, tab) -> Dict[str, Any]:
        """Locates specific data fields on the detail page."""
        elements: Dict[str, Any] = {}
        
        # 標題
        tab.wait.eles_loaded('tag:h1', timeout=10)
        title_ele = tab.ele('tag:h1')
        if title_ele:
            elements['title'] = title_ele
            
        # 總價
        price_ele = tab.ele('xpath://div[contains(@class, "buy_buy-content-title-price-first")]', timeout=2)
        if price_ele:
            elements['price'] = price_ele
            
        # 地址 (位於標題左側區塊)
        addr_ele = tab.ele('xpath://div[contains(@class, "buy_buy-content-title-left-area")]', timeout=2)
        if addr_ele:
            elements['address'] = addr_ele

        # 基本資料區塊
        tab.wait.eles_loaded('xpath://div[contains(@class, "buy_buy-content-basic")]', timeout=10)
        basic_block = tab.ele('xpath://div[contains(@class, "buy_buy-content-basic")]')
        
        if basic_block:
            elements['basic_block'] = basic_block
            
        return elements
