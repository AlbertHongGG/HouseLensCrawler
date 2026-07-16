import re
import time
import logging
from typing import Optional, Dict, Any

from ..base import BaseSpider
from ..factory import SpiderFactory
from ...engine.events import event_bus, Event
from ...engine.context import SpiderContext
from ...storage.interfaces import CheckStatus
from .navigator import Community591Navigator
from .transformer import Community591Transformer


@SpiderFactory.register("591_community")
class Community591Spider(BaseSpider):
    """
    591 房屋市集 - 社區資料爬蟲
    遵守 Container-based Locating 原則：先定位區塊，再往下尋找元素。
    """

    def __init__(self, config, **kwargs):
        super().__init__(config)
        self.navigator = Community591Navigator()
        self.transformer = Community591Transformer()

    @property
    def platform_name(self) -> str:
        return "591_community"

    def extract_source_id(self, url: str) -> Optional[str]:
        match = re.search(r'market\.591\.com\.tw/(\d+)', url)
        return match.group(1) if match else None

    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        使用 Container-based Locating 原則擷取社區資料。
        1. 先定位父容器 (Header Block, Info Block)
        2. 再透過父容器物件往下搜尋所需元素
        """
        raw_data = {}

        # ── 1. Header Block: 取得社區名稱 ──
        header_block = tab.ele('tag:h1', timeout=5)
        if header_block:
            raw_data['name'] = header_block.text.strip()
            self.raw_elements['name'] = header_block

        # ── 2. Info Block: 取得社區規格與地址 ──
        address = ""
        specs = {}
        info_block = tab.ele(
            'css:.community-info, .info-list, div[class*="info-container"], div[class*="detail-info"]',
            timeout=5
        )
        if info_block:
            self.raw_elements['specs'] = info_block

            # 在 info_block 容器內尋找 .info-item 元素
            info_items = info_block.eles('css:.info-item, li, div[class*="item"]')
            for item in info_items:
                text = item.text.strip().replace('\n', ' ')
                if not text:
                    continue

                # 解析 label: value 格式
                if "地址" in text:
                    address = text.replace("地址", "").strip().lstrip("：: ")
                    self.raw_elements['address'] = item
                elif "屋齡" in text:
                    specs["屋齡"] = text.replace("屋齡", "").strip().lstrip("：: ")
                elif "總戶數" in text:
                    specs["總戶數"] = text.replace("總戶數", "").strip().lstrip("：: ")
                elif "建築型態" in text:
                    specs["建築型態"] = text.replace("建築型態", "").strip().lstrip("：: ")
                elif "建設公司" in text:
                    specs["建設公司"] = text.replace("建設公司", "").strip().lstrip("：: ")
                elif "建築結構" in text:
                    specs["建築結構"] = text.replace("建築結構", "").strip().lstrip("：: ")
                elif "建築完成日" in text:
                    specs["建築完成日"] = text.replace("建築完成日", "").strip().lstrip("：: ")
                elif "土地使用分區" in text:
                    specs["土地使用分區"] = text.replace("土地使用分區", "").strip().lstrip("：: ")

        raw_data['address'] = address
        raw_data['specs'] = specs
        raw_data['source_id'] = self.extract_source_id(url) or ""
        raw_data['url'] = url

        return raw_data

    def process_detail_url(self, url: str, browser: Any, context: SpiderContext, force_scrape: bool = False) -> bool:
        """
        處理單一社區詳細頁面。
        流程：去重 → 開啟分頁 → 導航等待 → 擷取原始資料 → 視覺驗證 → 轉換 → 廣播事件
        """
        source_id = self.extract_source_id(url)
        if not source_id:
            logging.warning(f"[{self.platform_name}] Cannot extract source_id from: {url}")
            return False

        # 去重檢查
        status, original_url = context.register_item(source_id, url)
        if status == CheckStatus.LIMIT_REACHED:
            logging.info(f"[{self.platform_name}] {source_id} skipped (Limit Reached).")
            return False
        elif status == CheckStatus.DUPLICATE and not force_scrape:
            logging.info(f"[{self.platform_name}] {source_id} skipped (Duplicate).")
            event_bus.emit(Event.DUPLICATE_DETECTED,
                           platform=self.platform_name, source_id=source_id,
                           url_a=original_url, url_b=url)
            return False

        logging.info(f"[{self.platform_name}] Opening tab for community {source_id}...")
        detail_tab = None
        try:
            detail_tab = browser.new_tab(url)

            # 導航等待
            self.navigator.prepare_detail_page(detail_tab)

            # 擷取原始資料
            self.raw_elements.clear()
            raw_data = self.extract_raw_data(detail_tab, url)

            # 視覺驗證截圖
            if self.raw_elements:
                event_bus.emit(Event.ELEMENTS_LOCATED,
                               tab=detail_tab, elements=self.raw_elements,
                               source_id=source_id, platform_name=self.platform_name)

            # 資料轉換
            if not raw_data.get('name'):
                logging.warning(f"[{self.platform_name}] Missing community name for {url}")
                return False

            community = self.transformer.transform(raw_data)

            # 廣播社區資料已解析
            event_bus.emit(Event.COMMUNITY_PARSED, community=community)
            logging.info(f"[{self.platform_name}] Parsed community {source_id}: {community.name}")
            return True

        except Exception as e:
            logging.error(f"[{self.platform_name}] Error processing {source_id}: {e}", exc_info=True)
            return False
        finally:
            if detail_tab:
                detail_tab.close()
                time.sleep(0.5)
