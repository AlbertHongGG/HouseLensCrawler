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
