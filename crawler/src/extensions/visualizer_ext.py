import os
import logging
from typing import Any
from DrissionPage import ChromiumPage
from .base import BaseExtension
from ..engine.events import EventBus, Event

class VisualVerificationExtension(BaseExtension):
    """
    視覺化驗證外掛 (Extension)。
    主動監聽 `ELEMENTS_LOCATED` 事件，負責在網頁 DOM 元素上標記紅框與整頁截圖。
    """
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir

    def setup(self, bus: EventBus):
        # 註冊對 "尋找到 DOM 元素" 事件的監聽
        bus.subscribe(Event.ELEMENTS_LOCATED, self.on_elements_located)
        logging.info("[Extension] VisualVerificationExtension registered.")

    def on_elements_located(self, tab: ChromiumPage, elements: dict, source_id: str, platform_name: str, **kwargs):
        """事件處理常式：當 Spider 找到元素時，觸發標記與截圖"""
        # 1. 畫框
        for field_name, ele in elements.items():
            if ele:
                self.highlight(ele, field_name)
        
        # 2. 截圖
        filename = f"{source_id}.png"
        self.save_screenshot(tab, platform_name, filename)

    def highlight(self, ele: Any, label: str):
        if not ele:
            return

        js_script = f"""
        let el = this;
        let text = '{label}';
        if (window.getComputedStyle(el).position === 'static') {{
            el.style.position = 'relative';
        }}
        el.style.border = '3px solid red';
        el.style.boxSizing = 'border-box';
        
        let labelDiv = document.createElement('div');
        labelDiv.innerText = text;
        labelDiv.style.position = 'absolute';
        labelDiv.style.top = '-20px';
        labelDiv.style.left = '0';
        labelDiv.style.background = 'red';
        labelDiv.style.color = 'white';
        labelDiv.style.padding = '2px 5px';
        labelDiv.style.fontSize = '12px';
        labelDiv.style.fontWeight = 'bold';
        labelDiv.style.zIndex = '999999';
        labelDiv.style.whiteSpace = 'nowrap';
        labelDiv.style.pointerEvents = 'none';
        
        el.appendChild(labelDiv);
        """
        try:
            ele.run_js(js_script)
        except Exception as e:
            logging.debug(f"[Visualizer] Failed to highlight {label}: {e}")

    def save_screenshot(self, tab: ChromiumPage, spider_name: str, filename: str):
        target_dir = os.path.join(self.output_dir, spider_name)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, filename)
        try:
            logging.info(f"[Visualizer] Capturing full page screenshot to {filepath}...")
            tab.get_screenshot(path=filepath, full_page=True)
            logging.info(f"[Visualizer] Screenshot saved: {filename}")
        except Exception as e:
            logging.error(f"[Visualizer] Failed to take screenshot {filename}: {e}")
