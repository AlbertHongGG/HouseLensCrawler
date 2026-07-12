import time
import logging
from typing import List, Tuple
from DrissionPage import ChromiumPage

class Spider591Navigator:
    """
    負責在 591 網站上導航、滾動、翻頁以及提取清單 URL 的元件。
    """

    def __init__(self, platform_name: str = "591"):
        self.platform_name = platform_name

    def load_list_page(self, browser: ChromiumPage, url: str) -> bool:
        """
        [導航] 進入指定 URL，並處理反爬或 Lazy-loading。
        """
        logging.info(f"[{self.platform_name}] Loading page: {url}")
        browser.get(url)
        
        try:
            # 為了確保無頭瀏覽器不被阻擋，此處需滾動頁面觸發 Lazy Load
            browser.scroll.to_bottom()
            browser.scroll.to_top()
            is_loaded = browser.wait.ele_displayed('.ware-list-wrap', timeout=10)
            if not is_loaded:
                logging.warning(f"[{self.platform_name}] .ware-list-wrap not displayed yet, trying to proceed anyway.")
            return True
        except Exception as e:
            logging.error(f"[{self.platform_name}] Error loading list page: {e}")
            return False

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        """
        [提取] 從目前的清單頁中，過濾出所有真實物件的 URL。
        """
        wrap = browser.ele('.ware-list-wrap')
        if not wrap:
            logging.error(f"[{self.platform_name}] .ware-list-wrap not found.")
            return []
            
        # 尋找 ware-item，若改版則容錯尋找 housing-item
        items = wrap.eles('.ware-item')
        if not items:
            items = wrap.eles('.housing-item')
        
        urls_to_fetch = []
        for item in items:
            a_tag = item.ele('tag:a')
            if a_tag:
                href = a_tag.attr('href')
                # 排除廣告連結，確保是正常的 sale.591.com.tw 網址
                if href and 'sale.591.com.tw' in href:
                    urls_to_fetch.append(href)
                    
        return urls_to_fetch

    def go_next_page(self, browser: ChromiumPage) -> bool:
        """
        [導航] 尋找下一頁按鈕並點擊。若無法點擊或到達最後一頁則回傳 False。
        """
        try:
            # 尋找 span.navigator 並且底下有「下一頁」文字的 a 標籤
            next_span = browser.ele('xpath://span[contains(@class, "navigator") and .//a[contains(text(), "下一頁")]]', timeout=3)
            
            # 若 span 具有 disabled class，代表已經到了最後一頁
            if next_span and 'disabled' not in next_span.attr('class'):
                logging.info(f"[{self.platform_name}] Clicking next page...")
                next_btn = next_span.ele('tag:a')
                next_btn.click()
                browser.wait.load_start()
                time.sleep(1) # 給予一點時間讓 JS 渲染新的 list
                return True
            else:
                logging.info(f"[{self.platform_name}] No more pages or next button disabled.")
                return False
        except Exception as e:
            logging.warning(f"[{self.platform_name}] Error finding next page button: {e}")
            return False
