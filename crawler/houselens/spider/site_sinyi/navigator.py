import time
import logging
from typing import List
from DrissionPage import ChromiumPage
from ..components.navigators.base import BaseNavigator

class SinyiNavigator(BaseNavigator):
    def __init__(self, platform_name: str = "sinyi"):
        super().__init__(platform_name)

    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        list_url = f"{start_url}{page}"
        if not self.safe_get(browser, list_url):
            return False
            
        time.sleep(2) # 等待列表載入
        browser.wait.eles_loaded('xpath://div[contains(@id, "buyHouseCard_")]', timeout=5)
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        return self.wait_and_extract_links(browser, 'xpath://div[contains(@id, "buyHouseCard_")]')

    def prepare_detail_page(self, detail_tab: ChromiumPage):
        """
        [準備] 在開始抓取信義房屋詳細頁面資料前，嚴格等待基本資料區塊載入。
        """
        try:
            # 確保標題已出現
            detail_tab.wait.eles_loaded('xpath://span[contains(@class, "buy-content-title-name")]', timeout=10)
            
            # 確保基本資料區塊 (basic-info 或 buy_buy-content-basic) 已出現
            detail_tab.wait.eles_loaded('xpath://div[contains(@class, "buy_buy-content-basic") or contains(@id, "basic-data") or contains(@class, "buy-content-basic")]', timeout=10)
            
            # 往下滾動一點
            detail_tab.scroll.down(300)
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"[{self.platform_name}] Error preparing detail page: {e}")
