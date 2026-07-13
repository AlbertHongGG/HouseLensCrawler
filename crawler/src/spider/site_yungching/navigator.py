import time
import logging
from typing import List
from DrissionPage import ChromiumPage

from ..base_components import BaseNavigator

class SpiderYungchingNavigator(BaseNavigator):
    def __init__(self, platform_name: str = "yungching"):
        super().__init__(platform_name)

    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        list_url = f"{start_url}{page}"
        if not self.safe_get(browser, list_url):
            return False
            
        time.sleep(3) # Wait for Angular
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        return self.wait_and_extract_links(browser, 'css:li.m-list-item')
