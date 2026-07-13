import logging
from typing import Dict, Any, List
from DrissionPage import ChromiumPage

from ..base_components import BaseLocator

class SpiderYungchingLocator(BaseLocator):
    """
    負責在 Yungching (永慶房屋) 網頁上尋找並定位所有需要的 DOM 元素 (Locator 層)。
    """


    def locate_detail(self, tab: ChromiumPage) -> Dict[str, Any]:
        """
        從 Yungching 單一物件頁面擷取所有需要的欄位 Wrapper (元素)。
        """
        elements = {}
        
        # 先嘗試點擊「看詳細基本資訊」展開全部內容
        self.click_if_exists(tab, 'text:看詳細基本資訊', timeout=1.0)

        # 等待主要畫面載入
        tab.wait.eles_loaded('css:div.house-info', timeout=10)
        tab.wait.eles_loaded('css:div.detail-block.basic', timeout=10)
        
        house_info = tab.ele('css:div.house-info')
        if house_info:
            elements['title'] = house_info.ele('css:.case-name')
            elements['total_price'] = house_info.ele('xpath:.//*[contains(text(), "萬")]')
            elements['address'] = house_info.ele('css:.case-desc')
            
        basic_block = tab.ele('css:div.detail-block.basic', timeout=5)
        if basic_block:
            # 為了更細緻的 Highlight，我們迭代所有的 .item
            items = basic_block.eles('css:.item')
            for item in items:
                title_ele = item.ele('css:.item-title')
                if not title_ele:
                    continue
                title = title_ele.text
                
                if "建物格局" in title:
                    elements['layout'] = item
                if "建物坪數" in title:
                    elements['building_ping'] = item
                if "主建物" in title:
                    elements['main_building_ping'] = item
                if "共同使用小計" in title:
                    elements['shared_ping'] = item
                if "附屬建物小計" in title:
                    elements['accessory_ping'] = item
                if "土地坪數" in title:
                    elements['land_ping'] = item
                if "土地使用分區" in title:
                    elements['land_zoning'] = item
                if "謄本用途" in title:
                    elements['legal_usage'] = item
                if "房貸" in title:
                    elements['unit_price'] = item  # 單價通常跟房貸試算在同一 item 或其附近
                if "屋齡" in title:
                    elements['age'] = item
                if "社區" in title:
                    elements['community_name'] = item
                if "樓層" in title:
                    elements['floor'] = item
                if "管理費" in title:
                    elements['management_fee'] = item
                if "朝向" in title:
                    elements['orientation'] = item
                    
            has_parking_ele = basic_block.ele('車位數量', timeout=0.1)
            if has_parking_ele:
                elements['has_parking'] = has_parking_ele.parent('.item')
                
            titles = basic_block.eles('.item-title')
            for t in titles:
                t_text = t.text
                if '車位' in t_text and '數量' not in t_text:
                    item_ele = t.parent('.item')
                    if item_ele:
                        detail = item_ele.ele('.item-detail')
                        if detail:
                            elements['parking_type'] = detail
                            break
                        
            return elements
