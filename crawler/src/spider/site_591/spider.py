import re
import time
import logging

from ..base import BaseSpider
from .parser import Spider591Parser
from .navigator import Spider591Navigator
from ...storage.factory import StorageFactory
from ...engine.state import global_state
from ...engine.browser_pool import browser_pool

class Spider591(BaseSpider):
    """
    591 爬蟲的控制器 (Controller)。
    負責協調 Navigator (負責網頁導航) 與 Parser (負責資料解析)。
    此設計符合單一職責原則 (SRP)，使得主程式碼維持乾淨與高擴充性。
    """

    def __init__(self, config):
        super().__init__(config)
        self.navigator = Spider591Navigator(self.platform_name)
        self.parser = Spider591Parser(self.platform_name)

    @property
    def platform_name(self) -> str:
        return "591"

    def run(self):
        """
        [主流程] 執行完整的 591 爬蟲作業。
        """
        logging.info(f"[{self.platform_name}] Spider starting...")
        
        # 1. 取得全域資源
        storage = StorageFactory.get_storage()
        browser = browser_pool.get_browser()
        
        # 2. 從設定檔取得起始網址
        start_url = self.config.start_url
        if not start_url:
            logging.error(f"[{self.platform_name}] start_url is empty! Please check .env file.")
            return

        # 3. 進入首頁
        if not self.navigator.load_list_page(browser, start_url):
            return
            
        page = 1
        while page <= self.config.max_pages:
            # 檢查整體抓取數量上限
            if global_state.reached_limit(self.config.max_items):
                logging.info(f"[{self.platform_name}] Global limit reached ({self.config.max_items}). Stopping.")
                break

            logging.info(f"[{self.platform_name}] Parsing list page {page}...")
            
            # 4. 提取當前頁面的所有物件網址
            urls_to_fetch = self.navigator.extract_item_urls(browser)
            logging.info(f"[{self.platform_name}] Found {len(urls_to_fetch)} items on page {page}.")

            # 5. 逐一處理每個網址
            for url in urls_to_fetch:
                if global_state.reached_limit(self.config.max_items):
                    break
                    
                # [萃取 ID] e.g., .../detail/2/20136417.html
                match = re.search(r'detail/\d+/(\d+)\.html', url)
                if not match:
                    continue
                source_id = match.group(1)

                # [去重檢查]
                if not global_state.add_and_check(source_id, self.config.max_items):
                    logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Duplicate).")
                    continue
                
                logging.info(f"[{self.platform_name}] Opening tab for detail {source_id}...")
                
                # [開啟新分頁] 避免在同一個頁面反覆跳轉，這會導致 JS 崩潰與記憶體洩漏
                detail_tab = browser.new_tab(url)
                try:
                    # 交由 Parser 進行資料解析
                    prop = self.parser.parse_detail_page(detail_tab, url, source_id)
                    storage.save(prop)
                    logging.info(f"[{self.platform_name}] Saved detail {source_id}.")
                except Exception as e:
                    logging.error(f"[{self.platform_name}] Error parsing detail {source_id}: {e}")
                finally:
                    # [資源釋放] 確保分頁被關閉，維持最多只有 2 個 tab (主頁與詳情頁)
                    detail_tab.close()
                    time.sleep(0.5)

            if global_state.reached_limit(self.config.max_items):
                break

            # 6. 前往下一頁
            if not self.navigator.go_next_page(browser):
                break
                
            page += 1
        
        logging.info(f"[{self.platform_name}] Spider finished.")
