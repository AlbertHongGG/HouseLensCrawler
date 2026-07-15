import time
import logging
from typing import List
from DrissionPage import ChromiumPage
from ..components.navigators.base import BaseNavigator

class SinyiNavigator(BaseNavigator):
    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        list_url = f"{start_url}{page}"
        # wait, safe_get is not in BaseNavigator!
        browser.get(list_url)
        time.sleep(2) # 等待列表載入
        browser.wait.eles_loaded('xpath://div[contains(@id, "buyHouseCard_")]', timeout=5)
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        items = browser.eles('xpath://div[contains(@id, "buyHouseCard_")]//a[contains(@href, "/buy/house/")]')
        return [item.attr("href") for item in items if item.attr("href")]

    def prepare_detail_page(self, detail_tab: ChromiumPage):
        """
        [準備] 在開始抓取信義房屋詳細頁面資料前，嚴格等待基本資料區塊載入。
        """
        try:
            # 確保標題已出現
            detail_tab.wait.eles_loaded('css:h1, .buy-content-title-name', timeout=10)
            
            # 確保基本資料區塊 (basic-info 或 buy_buy-content-basic) 已出現
            detail_tab.wait.eles_loaded('css:div[class*="buy_buy-content-basic"], #basic-data, .buy-content-basic', timeout=10)
            
            # 往下滾動確保觸發 lazy load 圖片跟動態區塊
            for _ in range(5):
                detail_tab.scroll.down(500)
                time.sleep(0.3)
        except Exception as e:
            logging.warning(f"[{self.platform_name}] Error preparing detail page: {e}")
