import time
import logging
from typing import List
from DrissionPage import ChromiumPage
from ..components.navigators.base import BaseNavigator


class Community591Navigator(BaseNavigator):
    """
    Navigator for 591 Community pages.
    Handles page navigation, waiting, and scrolling.
    """

    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        """載入社區列表頁"""
        list_url = f"{start_url}?page={page}"
        browser.get(list_url)
        time.sleep(2)
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        """從列表頁提取社區詳細頁網址"""
        # 依據容器定位：section.list-container div.left-container a.community-card
        items = browser.eles('css:div.left-container a.community-card')
        return [item.attr("href") for item in items if item.attr("href")]

    def prepare_detail_page(self, detail_tab: ChromiumPage):
        """
        等待社區詳細頁面的關鍵區塊載入完畢。
        """
        try:
            # 等待標題載入
            detail_tab.wait.eles_loaded('tag:h1', timeout=10)

            # 等待資訊區塊載入
            detail_tab.wait.eles_loaded(
                'css:.info-item, .community-info, div[class*="info"]',
                timeout=10
            )

            # 往下滾動觸發 lazy load
            for _ in range(5):
                detail_tab.scroll.down(500)
                time.sleep(0.3)
        except Exception as e:
            logging.warning(f"[591_community] Error preparing detail page: {e}")
