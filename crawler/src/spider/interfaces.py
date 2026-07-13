from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from DrissionPage import ChromiumPage
from ..models.property import StandardProperty

class INavigator(ABC):
    @abstractmethod
    def load_list_page(self, browser: ChromiumPage, start_url: str, page: int) -> bool:
        """
        導航至指定的列表頁。
        如果該頁存在且載入成功，回傳 True；若已超過最大頁數或載入失敗，回傳 False。
        """
        pass

    @abstractmethod
    def extract_item_urls(self, browser: ChromiumPage) -> List[str]:
        """
        從當前列表頁擷取所有物件的 URL 列表。
        """
        pass

class ILocator(ABC):
    @abstractmethod
    def locate_detail(self, tab: ChromiumPage) -> Dict[str, Any]:
        """
        定位詳情頁中的各項 DOM 元素。
        回傳的 Dictionary 的 Key 將會被 Visualizer 用來標記方框的標籤，
        Value 則為對應的 DrissionPage 元素 (ChromiumElement)。
        """
        pass

class IParser(ABC):
    @abstractmethod
    def extract_source_id(self, url: str) -> str:
        """
        從網址中擷取該平台的唯一物件識別碼 (source_id)。
        例如從 `https://sale.591.com.tw/home/house/detail/2/20136417.html` 擷取出 `20136417`。
        """
        pass

    @abstractmethod
    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        """
        將 Locator 取得的 DOM 元素進行清理與轉換，輸出 StandardProperty 物件。
        如果該物件解析失敗或無效，回傳 None。
        """
        pass
