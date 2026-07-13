import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from DrissionPage import ChromiumPage

from .interfaces import INavigator, ILocator, IParser

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

class BaseLocator(ILocator):
    def click_if_exists(self, tab: ChromiumPage, text_or_css: str, timeout: float = 1.0):
        try:
            btn = tab.ele(text_or_css, timeout=timeout)
            if btn:
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass

class BaseParser(IParser):
    def __init__(self, platform_name: str = ""):
        self.platform_name = platform_name
        
    def extract_float(self, text: str) -> float:
        if not text: return 0.0
        # 移除 , 等雜訊
        clean_str = str(text).replace(',', '').replace('\n', '').replace(' ', '')
        match = re.search(r'[\d.]+', clean_str)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return 0.0
        return 0.0

    def extract_int(self, text: str) -> int:
        if not text: return 0
        clean_str = str(text).replace(',', '').replace('\n', '').replace(' ', '')
        match = re.search(r'\d+', clean_str)
        if match:
            try:
                return int(match.group())
            except ValueError:
                return 0
        return 0

    def clean_text(self, ele: Any, label: str = "") -> str:
        if not ele: return ""
        if isinstance(ele, str):
            val = ele
        else:
            val = ele.text
            
        if label:
            val = val.replace(' ', '').replace('\n', '').replace('：', '').replace(':', '')
            val = val.replace(label, '').strip()
        else:
            # 移除多餘空白、tab、換行
            val = re.sub(r'[\r\n\t\s]+', ' ', val).strip()
            
        if len(val) < 100:
            return val
        return ""

    def parse_ping(self, text: str, label: str = "") -> float:
        if label and label in text:
            # e.g., "主建物小計 10.5 坪" -> "10.5 坪"
            text = text.split(label)[-1]
        return self.extract_float(text)

    def parse_age(self, text: str) -> float:
        return self.extract_float(text)

    def parse_floor(self, text: str) -> Tuple[str, str]:
        # e.g., "2樓/共5樓" -> floor="2樓", total_floors="5樓"
        floor, total_floors = "", ""
        if not text: return floor, total_floors
        
        parts = text.split('/')
        if len(parts) == 2:
            floor = parts[0].strip()
            total_floors = parts[1].replace('共', '').strip()
        else:
            floor = text.strip()
        return floor, total_floors

    def parse_layout(self, text: str) -> Dict[str, int]:
        layout = {"rooms": 0, "living_rooms": 0, "bathrooms": 0, "kitchens": 0, "balconies": 0}
        if not text: return layout
        
        patterns = {
            "rooms": r'(\d+)\s*房',
            "living_rooms": r'(\d+)\s*廳',
            "bathrooms": r'(\d+)\s*衛',
            "kitchens": r'(\d+)\s*(?:廚|室)',
            "balconies": r'(\d+)\s*陽台'
        }
        for k, p in patterns.items():
            m = re.search(p, text)
            if m:
                # balcony 有可能匹配到 group(1) 或是 group(2)
                val = m.group(1) if m.group(1) else m.group(2)
                if val:
                    layout[k] = int(val)
        return layout

    def extract_after(self, text: str, keyword: str) -> str:
        """從字串中擷取指定關鍵字之後的文字"""
        if keyword in text:
            return text.split(keyword)[-1].strip()
        return ""
