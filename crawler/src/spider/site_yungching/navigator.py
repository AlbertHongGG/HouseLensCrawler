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
        
        # 關閉「AI找房」的彈出視窗 (如果存在)
        try:
            close_btn = browser.ele('.ai-find-hint-close', timeout=1)
            if close_btn:
                close_btn.click()
                time.sleep(0.5)
        except Exception:
            pass
            
        return True

    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        try:
            # 等待卡片載入，Yungching 新版 Angular 網站使用 a.link 或者是包覆在內的 a 標籤
            # 先等待任意一個物件卡片出現，最多等 5 秒
            try:
                browser.wait.eles_loaded('tag:a', timeout=5)
            except Exception:
                pass
                
            # 找到所有 a 標籤
            a_tags = browser.eles('tag:a', timeout=0)
            
            links = []
            for a_tag in a_tags:
                href = a_tag.attr('href')
                # 判斷是否為物件詳細頁的連結 (e.g., https://buy.yungching.com.tw/house/...)
                if href and '/house/' in href:
                    if href not in links:
                        links.append(href)
            
            import logging
            logging.info(f"[{self.platform_name}] Extracted {len(links)} links using 'tag:a'")
            return links
        except Exception as e:
            import logging
            logging.error(f"[{self.platform_name}] Error extracting links: {e}")
            return []
