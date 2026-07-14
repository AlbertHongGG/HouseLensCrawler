import logging
from typing import List
from DrissionPage import ChromiumPage

from .interface import INavigator

class BaseNavigator(INavigator):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    def safe_get(self, browser: ChromiumPage, url: str) -> bool:
        try:
            logging.info(f"[{self.platform_name}] Loading page: {url}")
            browser.get(url)
            return True
        except Exception as e:
            logging.error(f"[{self.platform_name}] Error loading page {url}: {e}")
            return False

    def wait_and_extract_links(self, browser: ChromiumPage, css_selector: str) -> List[str]:
        try:
            browser.wait.eles_loaded(css_selector, timeout=5)
            items = browser.eles(css_selector, timeout=0)
            links = []
            for item in items:
                a_tag = item.ele('tag:a', timeout=1)
                if a_tag:
                    href = a_tag.attr('href')
                    if href:
                        links.append(href)
            return links
        except Exception as e:
            logging.error(f"[{self.platform_name}] Error extracting links for selector {css_selector}: {e}")
            return []
