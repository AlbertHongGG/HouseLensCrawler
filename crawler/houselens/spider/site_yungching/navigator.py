import time
import logging
from typing import List, Any
from ..components.navigators.base import BaseNavigator

class SpiderYungchingNavigator(BaseNavigator):
    def __init__(self):
        super().__init__()
        self.platform_name = "yungching"

    def load_list_page(self, browser: Any, start_url: str, page: int) -> bool:
        list_url = f"{start_url}{page}"
        browser.get(list_url)
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

    def extract_item_urls(self, browser: Any) -> List[str]:
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
            
            logging.info(f"[{self.platform_name}] Extracted {len(links)} links using 'tag:a'")
            return links
        except Exception as e:
            logging.error(f"[{self.platform_name}] Error extracting links: {e}")
            return []

    def prepare_detail_page(self, detail_tab: Any):
        """[準備] 點擊 '看詳細基本資訊' 以展開規格表，並確保畫面載入"""
        try:
            # 確保標題已出現
            detail_tab.wait.eles_loaded('tag:h1', timeout=10)
            
            # 永慶的詳細資訊通常需要點擊才能完全顯示在 DOM 中
            btn = detail_tab.ele('text:看詳細基本資訊', timeout=1)
            if btn:
                btn.click()
                time.sleep(1) # 等待動畫或渲染
                
            # 確保房屋資料區塊出現
            detail_tab.wait.eles_loaded('css:.detail-block.basic, .house-detail-info', timeout=2)
            
            detail_tab.scroll.down(500)
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"[{self.platform_name}] Error preparing detail page: {e}")
