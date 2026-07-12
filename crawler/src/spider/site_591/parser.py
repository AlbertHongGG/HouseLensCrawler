import re
import uuid
from typing import Optional
from DrissionPage import ChromiumPage
from ...models.property import StandardProperty

class Spider591Parser:
    """
    負責解構 591 網頁 DOM 結構的解析器。
    確保所有的字串處理、正則提取、標籤尋找邏輯集中於此，提高維護性。
    """
    
    def __init__(self, platform_name: str = "591"):
        self.platform_name = platform_name

    def _extract_float(self, text: str) -> Optional[float]:
        """
        [工具] 從字串中萃取浮點數，去除逗號與雜訊。
        例如 "1,200.5萬" -> 1200.5
        """
        if not text:
            return None
        match = re.search(r'[\d\.]+', text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def _get_value(self, tab: ChromiumPage, label: str) -> str:
        """
        [工具] 透過尋找標籤文字，取得其母元素的完整文字，再過濾掉標籤本身。
        這種作法可以無視 591 隨機將數值放在標籤上方、下方或右側相鄰元素的排版變動。
        """
        try:
            # 使用精準的 xpath 找到包含 label 的最深層元素
            ele = tab.ele(f'xpath://*[text()="{label}"]', timeout=0.5)
            if not ele:
                # 容錯：有時可能帶有空白
                ele = tab.ele(f'xpath://*[contains(text(), "{label}")]', timeout=0.5)
                
            if ele:
                parent = ele.parent()
                if parent:
                    # 取得 parent 全文，並剔除 label 與冒號等雜訊
                    raw_text = parent.text
                    val = raw_text.replace(label, '').replace('：', '').replace(':', '').strip()
                    # 避免抓到外層大區塊導致字串過長
                    if len(val) < 100:
                        return val
        except Exception:
            pass
        return ""

    def parse_detail_page(self, tab: ChromiumPage, url: str, source_id: str) -> StandardProperty:
        """
        [解析核心] 從 591 物件詳細頁中提取資訊並對應到 StandardProperty。
        """
        tab.wait.eles_loaded('xpath://h1', timeout=5)
        
        # [1] 基本屬性：標題、總價、單價
        title_ele = tab.ele('xpath://h1', timeout=1)
        title = title_ele.text if title_ele else f"591物件 {source_id}"

        price_ele = tab.ele('xpath://*[contains(@class, "price")]', timeout=1)
        total_price_str = price_ele.text if price_ele else "0"
        total_price = self._extract_float(total_price_str) or 0.0

        unit_price_ele = tab.ele('xpath://*[contains(text(), "萬/坪")]', timeout=1)
        unit_price = self._extract_float(unit_price_ele.text) if unit_price_ele else 0.0

        # [2] 結構屬性：格局、屋齡、權狀坪數、樓層
        layout = self._get_value(tab, '格局')
        age = self._extract_float(self._get_value(tab, '屋齡')) or 0.0
        building_ping = self._extract_float(self._get_value(tab, '權狀坪數')) or 0.0
        
        floor = ""
        total_floor = ""
        floor_text = self._get_value(tab, '樓層')
        if '/' in floor_text:
            floor, total_floor = floor_text.split('/', 1)
        else:
            floor = floor_text

        # [3] 地理與社群：地址、社區名稱
        address = self._get_value(tab, '地址')
        community_name = self._get_value(tab, '社區')

        # [4] 詳細資訊區塊：型態、車位、坪數細節
        raw_building_type = self._get_value(tab, "型態")
        management_fee = self._get_value(tab, "管理費")
        
        has_tenant_str = self._get_value(tab, "帶租約")
        has_tenant = "是" in has_tenant_str if has_tenant_str else None
        
        legal_usage = self._get_value(tab, "法定用途")
        
        parking_str = self._get_value(tab, "車位")
        has_parking = "無" not in parking_str if parking_str else None
        parking_ping = self._extract_float(parking_str) if has_parking else None

        main_ping = self._extract_float(self._get_value(tab, "主建物"))
        accessory_ping = self._extract_float(self._get_value(tab, "附屬建物"))
        shared_ping = self._extract_float(self._get_value(tab, "共用部分"))
        land_ping = self._extract_float(self._get_value(tab, "土地坪數"))

        # [5] 組裝與映射：產生標準物件
        return StandardProperty(
            property_uuid=str(uuid.uuid4()),
            source_platform=self.platform_name,
            source_id=source_id,
            title=title,
            total_price=total_price,
            unit_price=unit_price,
            building_ping=building_ping,
            layout=layout,
            age=age,
            floor=floor.strip(),
            total_floor=total_floor.strip(),
            address=address,
            url=url,
            raw_building_type=raw_building_type,
            main_building_ping=main_ping,
            accessory_ping=accessory_ping,
            shared_ping=shared_ping,
            land_ping=land_ping,
            has_parking=has_parking,
            parking_type=parking_str,
            parking_ping=parking_ping,
            legal_usage=legal_usage,
            has_tenant=has_tenant,
            community_name=community_name,
            management_fee=management_fee
        )
