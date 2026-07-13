import time
import logging
from typing import List
from DrissionPage import ChromiumPage

from ..interfaces import INavigator

class SpiderYungchingNavigator(INavigator):
    def __init__(self, platform_name: str = "yungching"):
        self.platform_name = platform_name

    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        list_url = f"{start_url}{page}"
        logging.info(f"[{self.platform_name}] Loading page: {list_url}")
        browser.get(list_url)
        time.sleep(3) # Wait for Angular
        
        # 簡單判斷是否成功載入 (透過尋找卡片)
        # 永慶的卡片通常是 .m-list-item 
        browser.wait.eles_loaded('.m-list-item', timeout=5)
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        items = browser.eles('.m-list-item', timeout=0)
        
        links = []
        for item in items:
            a_tag = item.ele('tag:a', timeout=1)
            if a_tag:
                href = a_tag.attr('href')
                if href:
                    links.append(href)
        return links
