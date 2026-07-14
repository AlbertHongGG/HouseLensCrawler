from abc import ABC, abstractmethod
from typing import List
from DrissionPage import ChromiumPage

class INavigator(ABC):
    """
    Navigator 負責定義在網頁間跳轉與抓取列表連結的介面。
    """
    @abstractmethod
    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        """載入目標列表頁"""
        pass

    @abstractmethod
    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        """提取列表頁上的所有物件網址"""
        pass

    def prepare_detail_page(self, detail_tab: ChromiumPage):
        """(Optional) 在擷取資料前，對物件詳細頁進行預先操作 (例如：點擊展開按鈕)"""
        pass
