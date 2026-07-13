import time
import logging
from typing import List
from DrissionPage import ChromiumPage

from ..interfaces import INavigator

class SinyiNavigator(INavigator):
    def __init__(self, platform_name: str = "sinyi"):
        self.platform_name = platform_name

    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        list_url = f"{start_url}{page}"
        logging.info(f"[{self.platform_name}] Loading page: {list_url}")
        browser.get(list_url)
        time.sleep(2) # 等待列表載入
        
        # 簡單判斷是否成功載入 (透過尋找卡片)
        browser.wait.eles_loaded('xpath://div[contains(@id, "buyHouseCard_")]', timeout=5)
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        items = browser.eles('xpath://div[contains(@id, "buyHouseCard_")]', timeout=0)
        
        links = []
        for item in items:
            a_tag = item.ele('tag:a', timeout=1)
            if a_tag:
                href = a_tag.attr('href')
                if href:
                    links.append(href)
        return links
