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
        if page == 1:
            browser.get(start_url)
            time.sleep(2)
            return True
        else:
            return self._go_next_page(browser)

    def _go_next_page(self, browser: ChromiumPage) -> bool:
        """
        [導航] 尋找下一頁按鈕並點擊。若無法點擊或到達最後一頁則回傳 False。
        """
        try:
            # 尋找 span.navigator 並且底下有「下一頁」文字的 a 標籤
            next_span = browser.ele('xpath://span[contains(@class, "navigator") and .//a[contains(text(), "下一頁")]]', timeout=3)
            
            # 若 span 具有 disabled class，代表已經到了最後一頁
            if next_span and 'disabled' not in next_span.attr('class'):
                logging.info(f"[591_community] Clicking next page...")
                next_btn = next_span.ele('tag:a')
                next_btn.click()
                browser.wait.load_start()
                time.sleep(1) # 給予一點時間讓 JS 渲染新的 list
                return True
            else:
                logging.info(f"[591_community] No more pages or next button disabled.")
                return False
        except Exception as e:
            logging.warning(f"[591_community] Error finding next page button: {e}")
            return False

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
