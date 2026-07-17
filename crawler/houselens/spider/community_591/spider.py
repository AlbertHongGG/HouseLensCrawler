import re
import time
import logging
from typing import Optional, Dict, Any

from ..base import BaseSpider
from ..factory import SpiderFactory
from ...engine.events import event_bus, Event
from ...engine.context import SpiderContext
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
    def target_event(self) -> Event:
        return Event.COMMUNITY_PARSED

    @property
    def platform_name(self) -> str:
        return "591_community"

    def extract_source_id(self, url: str) -> Optional[str]:
        match = re.search(r'market\.591\.com\.tw/(\d+)', url)
        return match.group(1) if match else None

    def extract_raw_data(self, tab: Any, url: str) -> Dict[str, Any]:
        """
        擷取社區主頁的基本資料與封面圖。
        """
        raw_data = {}
        specs = {}
        
        # 1. 名稱
        header_block = tab.ele('tag:h1', timeout=5)
        if header_block:
            raw_data['name'] = header_block.text.strip()
            self.raw_elements['name'] = header_block

        # 2. 封面圖片
        img_ele = tab.ele('css:img[alt*="封面"], .swiper-slide-active img, .intro-photo-preview img', timeout=2)
        if img_ele:
            raw_data['image_url'] = img_ele.attr('src')
            self.raw_elements['image'] = img_ele
            
        # 3. 提取地址、屋齡、總戶數等資訊
        info_block = tab.ele('css:.intro-info-container, .detail-info', timeout=5)
        if info_block:
            # 抓取包含文字的區塊進行比對
            items = info_block.eles('tag:div') + info_block.eles('tag:p') + info_block.eles('tag:li')
            for item in items:
                text = item.text.strip().replace('\n', ' ')
                if not text:
                    continue
                
                # 地址常出現在城市標籤或麵包屑區塊
                if "市" in text and "區" in text and ("路" in text or "街" in text or "段" in text):
                    raw_data['address'] = text.strip()
                    self.raw_elements['address'] = item
                    
                if "屋齡" in text:
                    specs["屋齡"] = text.replace("屋齡", "").strip()
                    self.raw_elements['age'] = item if item.tag in ['li', 'div', 'p'] else item.parent()
                elif "總戶數" in text:
                    specs["總戶數"] = text.replace("總戶數", "").strip()
                    self.raw_elements['total_households'] = item if item.tag in ['li', 'div', 'p'] else item.parent()
                elif "建築完成日" in text:
                    specs["建築完成日"] = text.replace("建築完成日", "").strip()
                    self.raw_elements['completion_date'] = item if item.tag in ['li', 'div', 'p'] else item.parent()

        raw_data['specs'] = specs
        raw_data['source_id'] = self.extract_source_id(url) or ""
        raw_data['url'] = url

        return raw_data

    def extract_overview_data(self, tab: Any) -> Dict[str, Any]:
        """
        擷取 /overview 頁面的社區規劃與建築設計資料。
        """
        specs = {}
        
        def _get_container(ele):
            if not ele: return None
            return ele.parent() if len(ele.text.strip()) <= 10 else ele

        # 社區規劃區塊
        planning_title = tab.ele('xpath://h3[contains(@class, "overview-title") and contains(text(), "社區規劃")]', timeout=3)
        if planning_title:
            planning_block = planning_title.parent()
            if planning_block:
                text = planning_block.text.replace('\n', ' ')
                specs['building_structure'] = text
                specs['land_zoning'] = text
                
                # 精確標示個別項目
                struct_item = planning_block.ele('text:建築構造')
                if struct_item: self.raw_elements['building_structure'] = _get_container(struct_item)
                
                zoning_item = planning_block.ele('text:土地分區')
                if zoning_item: self.raw_elements['land_zoning'] = _get_container(zoning_item)

        # 建築設計區塊
        design_title = tab.ele('xpath://h3[contains(@class, "overview-title") and contains(text(), "建築設計")]', timeout=3)
        if design_title:
            design_block = design_title.parent()
            if design_block:
                text = design_block.text.replace('\n', ' ')
                specs['builder'] = text
                
                # 精確標示個別項目
                builder_item = design_block.ele('text:投資建設') or design_block.ele('text:建設公司')
                if builder_item: self.raw_elements['builder'] = _get_container(builder_item)
                
                contractor_item = design_block.ele('text:營造公司')
                if contractor_item: self.raw_elements['contractor'] = _get_container(contractor_item)
                
        return specs

    def process_detail_url(self, url: str, browser: Any, context: SpiderContext, force_scrape: bool = False) -> bool:
        """
        處理單一社區詳細頁面。
        流程：去重 → 開啟分頁 → 主頁擷取(截圖) → Overview頁擷取(截圖) → 轉換 → 廣播事件
        """
        source_id = self.extract_source_id(url)
        if not source_id:
            return False

        if not context.try_acquire_item():
            logging.info(f"[{self.platform_name}] Detail {source_id} skipped (Limit Reached).")
            return False
            
        logging.info(f"[{self.platform_name}] Scraping detail: {url}")
        detail_tab = None
        try:
            detail_tab = browser.new_tab(url)

            # --- Stage 1: 主頁 ---
            self.navigator.prepare_detail_page(detail_tab)
            self.raw_elements.clear()
            raw_data = self.extract_raw_data(detail_tab, url)

            if self.raw_elements:
                event_bus.emit(Event.ELEMENTS_LOCATED,
                               tab=detail_tab, elements=self.raw_elements.copy(),
                               source_id=f"{source_id}_main", platform_name=self.platform_name)

            if not raw_data.get('name'):
                logging.warning(f"[{self.platform_name}] Missing community name for {url}")
                return False

            # --- Stage 2: Overview 頁面 ---
            overview_url = f"{url}/overview" if not url.endswith("/overview") else url
            logging.info(f"[{self.platform_name}] Navigating to overview: {overview_url}")
            detail_tab.get(overview_url)
            time.sleep(2)
            
            self.raw_elements.clear()
            overview_specs = self.extract_overview_data(detail_tab)
            
            # 合併規格資料
            raw_data['specs'].update(overview_specs)
            
            if self.raw_elements:
                event_bus.emit(Event.ELEMENTS_LOCATED,
                               tab=detail_tab, elements=self.raw_elements.copy(),
                               source_id=f"{source_id}_overview", platform_name=self.platform_name)

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
