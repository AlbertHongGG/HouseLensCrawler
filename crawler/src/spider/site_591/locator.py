from typing import Dict, Optional, Any
from DrissionPage import ChromiumPage

class Spider591Locator:
    """
    負責在 591 網頁上尋找並定位所有需要的 DOM 元素 (Locator 層)。
    符合單一職責原則：不涉及任何字串切割、清理或轉型，純粹產出元素字典。
    """
    
    def _get_parent_ele(self, container: Any, label: str) -> Optional[Any]:
        """
        [工具] 透過標籤文字在特定的 Container 內尋找，回傳其母元素。
        """
        if not container:
            return None
        try:
            # 注意 xpath 開頭為 .// 代表在當前節點下搜尋
            ele = container.ele(f'xpath:.//*[text()="{label}"]', timeout=0)
            if not ele:
                ele = container.ele(f'xpath:.//*[contains(text(), "{label}")]', timeout=0)
            if ele:
                return ele.parent()
        except Exception:
            pass
        return None

    def locate(self, tab: ChromiumPage) -> Dict[str, Any]:
        """
        定位詳細頁面的所有目標元素，回傳字典以供 Visualizer 與 Parser 使用。
        """
        # 等待主要畫面載入，並確保 Vue 區塊已渲染
        tab.wait.eles_loaded('xpath://h1', timeout=5)
        
        import time
        t0 = time.time()
        # 等待 Vue 將 ${title} 等佔位符替換為實際資料
        while True:
            h1 = tab.ele('xpath://h1', timeout=0)
            if h1 and '${title}' not in h1.text:
                break
            if time.time() - t0 > 5:
                break
            time.sleep(0.1)
            
        tab.wait.eles_loaded('.info-box-price-2', timeout=5)
        
        elements = {}
        
        # === 抓取各大容器 Container ===
        title_container = tab.ele('.detail-title-container', timeout=0)
        info_container = tab.ele('#new-vue-sale-detail-info', timeout=0)
        nav_vue_root = tab.ele('#detail-nav-vue-root', timeout=0)
        
        # 尋找房屋資料區塊
        house_boxes = tab.eles('.detail-house-box', timeout=0)
        house_data_box = None
        for box in house_boxes:
            if "型態" in box.text or "房屋資料" in box.text:
                house_data_box = box
                break
                
        # [1] 標題區塊
        elements['title'] = title_container.ele('xpath:.//h1', timeout=0) if title_container else None
        
        # [2] Info 區塊 (價格、樓層、地址)
        if info_container:
            price_box = info_container.ele('.info-box-price-2', timeout=0)
            floor_box = info_container.ele('.info-box-floor', timeout=0)
            addr_box = info_container.ele('.info-box-addr', timeout=0)
            
            if price_box:
                elements['total_price'] = price_box.ele('xpath:.//*[contains(@class, "price")]', timeout=0)
                elements['unit_price'] = price_box.ele('xpath:.//*[contains(text(), "萬/坪")]', timeout=0)
                
            if floor_box:
                elements['building_ping'] = self._get_parent_ele(floor_box, '權狀坪數')
                elements['layout'] = self._get_parent_ele(floor_box, '格局')
                elements['age'] = self._get_parent_ele(floor_box, '屋齡')
                
            if addr_box:
                elements['floor_info'] = self._get_parent_ele(addr_box, '樓層')
                elements['address'] = self._get_parent_ele(addr_box, '地址')
                elements['community_name'] = self._get_parent_ele(addr_box, '社區')
                elements['orientation'] = self._get_parent_ele(addr_box, '朝向')
                
        # [3] 房屋資料區塊
        if house_data_box:
            elements['raw_building_type'] = self._get_parent_ele(house_data_box, '型態')
            elements['management_fee'] = self._get_parent_ele(house_data_box, '管理費')
            elements['has_tenant'] = self._get_parent_ele(house_data_box, '帶租約')
            elements['legal_usage'] = self._get_parent_ele(house_data_box, '法定用途')
            elements['parking_info'] = self._get_parent_ele(house_data_box, '車位')
            
        # [4] 坪數說明區塊
        if nav_vue_root:
            elements['main_building_ping'] = self._get_parent_ele(nav_vue_root, '主建物')
            elements['accessory_ping'] = self._get_parent_ele(nav_vue_root, '附屬建物')
            elements['shared_ping'] = self._get_parent_ele(nav_vue_root, '共用部分')
            elements['land_ping'] = self._get_parent_ele(nav_vue_root, '土地坪數')
            
        return elements
