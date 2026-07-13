from typing import Dict, Optional, Any
from DrissionPage import ChromiumPage

class Spider591Locator:
    """
    負責在 591 網頁上尋找並定位所有需要的 DOM 元素 (Locator 層)。
    符合單一職責原則：不涉及任何字串切割、清理或轉型，純粹產出元素字典。
    """
    
    def _get_parent_ele(self, tab: ChromiumPage, label: str) -> Optional[Any]:
        """
        [工具] 透過標籤文字尋找，回傳其母元素。
        """
        try:
            # 使用極短的 timeout，因為在進入此函數前，主結構已經 loaded。
            # 如果欄位不存在，就不該白白浪費秒數等待。
            ele = tab.ele(f'xpath://*[text()="{label}"]', timeout=0)
            if not ele:
                ele = tab.ele(f'xpath://*[contains(text(), "{label}")]', timeout=0)
            if ele:
                return ele.parent()
        except Exception:
            pass
        return None

    def locate(self, tab: ChromiumPage) -> Dict[str, Any]:
        """
        定位詳細頁面的所有目標元素，回傳字典以供 Visualizer 與 Parser 使用。
        """
        # 等待主要畫面載入
        tab.wait.eles_loaded('xpath://h1', timeout=5)
        
        elements = {}
        
        # [1] 基本屬性
        elements['title'] = tab.ele('xpath://h1', timeout=0)
        elements['total_price'] = tab.ele('xpath://*[contains(@class, "price")]', timeout=0)
        elements['unit_price'] = tab.ele('xpath://*[contains(text(), "萬/坪")]', timeout=0)
        
        # [2] 結構屬性
        elements['layout'] = self._get_parent_ele(tab, '格局')
        elements['age'] = self._get_parent_ele(tab, '屋齡')
        elements['building_ping'] = self._get_parent_ele(tab, '權狀坪數')
        elements['floor_info'] = self._get_parent_ele(tab, '樓層')
        
        # [3] 地理與社群
        elements['address'] = self._get_parent_ele(tab, '地址')
        elements['community_name'] = self._get_parent_ele(tab, '社區')
        
        # [4] 詳細資訊區塊
        elements['raw_building_type'] = self._get_parent_ele(tab, '型態')
        elements['management_fee'] = self._get_parent_ele(tab, '管理費')
        elements['has_tenant'] = self._get_parent_ele(tab, '帶租約')
        elements['legal_usage'] = self._get_parent_ele(tab, '法定用途')
        elements['parking_info'] = self._get_parent_ele(tab, '車位')
        
        # 坪數細節
        elements['main_building_ping'] = self._get_parent_ele(tab, '主建物')
        elements['accessory_ping'] = self._get_parent_ele(tab, '附屬建物')
        elements['shared_ping'] = self._get_parent_ele(tab, '共用部分')
        elements['land_ping'] = self._get_parent_ele(tab, '土地坪數')
        
        return elements
