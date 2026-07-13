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
        
        // 取得元素的絕對位置與尺寸
        let rect = el.getBoundingClientRect();
        let bodyRect = document.body.getBoundingClientRect();
        
        // 建立透明度遮罩框 (Overlay) - 不直接修改原素，避免破壞排版
        let overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        // 利用相對於 body 的座標來定位，徹底解決 scrollY 與 margin 造成的偏移問題
        overlay.style.top = (rect.top - bodyRect.top) + 'px';
        overlay.style.left = (rect.left - bodyRect.left) + 'px';
        overlay.style.width = rect.width + 'px';
        overlay.style.height = rect.height + 'px';
        overlay.style.backgroundColor = 'rgba(0, 150, 255, 0.15)'; // 淡藍色半透明背景，不遮擋文字
        overlay.style.border = '2px dashed #0096FF'; // 藍色虛線邊框
        overlay.style.boxSizing = 'border-box';
        overlay.style.pointerEvents = 'none'; // 讓滑鼠可以穿透
        overlay.style.zIndex = '2147483646'; // 極高層級
        overlay.style.borderRadius = '4px';
        
        // 建立標籤 (Label)
        let labelDiv = document.createElement('div');
        labelDiv.innerText = text;
        labelDiv.style.position = 'absolute';
        // 將 Label 放在框框的左上角上方，避免擋住框內的文字
        labelDiv.style.top = (rect.top - bodyRect.top - 22) + 'px';
        labelDiv.style.left = (rect.left - bodyRect.left) + 'px';
        labelDiv.style.backgroundColor = '#0096FF';
        labelDiv.style.color = '#ffffff';
        labelDiv.style.padding = '2px 8px';
        labelDiv.style.fontSize = '12px';
        labelDiv.style.fontWeight = 'bold';
        labelDiv.style.fontFamily = 'sans-serif';
        labelDiv.style.borderRadius = '4px';
        labelDiv.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)'; // 增加陰影提升質感
        labelDiv.style.zIndex = '2147483647';
        labelDiv.style.whiteSpace = 'nowrap';
        labelDiv.style.pointerEvents = 'none';
        
        // 將元素加到 body 的最外層，徹底解決 overflow: hidden 導致的截斷問題
        document.body.appendChild(overlay);
        document.body.appendChild(labelDiv);
        """
        try:
            ele.run_js(js_script)
        except Exception as e:
            logging.debug(f"[Visualizer] Failed to highlight {label}: {e}")

    def save_screenshot(self, tab: ChromiumPage, spider_name: str, filename: str):
        target_dir = os.path.join(self.output_dir, spider_name)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, filename)
        import base64
        import time

        # ==========================================
        # 1. 向下捲動以觸發所有 Lazy Load 圖片
        # ==========================================
        try:
            height = int(tab.run_js('return document.documentElement.scrollHeight'))
            # 每次捲動 800px，直到頁尾
            for i in range(0, height, 800):
                tab.run_js(f'window.scrollTo(0, {i})')
                time.sleep(0.05)
            # 捲動回最上方
            tab.run_js('window.scrollTo(0, 0)')
            time.sleep(0.5)
        except Exception as e:
            pass # 忽略捲動錯誤

        # ==========================================
        # 2. 計算頁面總尺寸與 DPI，避免硬體紋理溢位
        # ==========================================
        # 直接截取原始的 scrollWidth 和 scrollHeight，不再自作聰明進行裁切
        # 這樣就不會切到 Header, Footer 或右側浮動按鈕。
        # 同時考慮 devicePixelRatio，避免超過 Chrome 的硬體紋理限制 (16384 physical pixels)
        # 如果超過，則等比例縮小 (scale < 1)
        clip_js = """
        let logicalWidth = document.documentElement.scrollWidth;
        let logicalHeight = document.documentElement.scrollHeight;
        let dpr = window.devicePixelRatio || 1;
        let maxLogicalHeight = 16000 / dpr; // 保守抓 16000 實體像素上限
        
        let scale = 1.0;
        if (logicalHeight > maxLogicalHeight) {
            scale = maxLogicalHeight / logicalHeight;
        }
        
        return {
            x: 0, 
            y: 0, 
            width: logicalWidth, 
            height: logicalHeight,
            scale: scale
        };
        """
        
        try:
            clip = tab.run_js(clip_js)
            result = tab.run_cdp('Page.captureScreenshot', 
                format='png', 
                captureBeyondViewport=True, 
                clip=clip
            )
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(result['data']))
        except Exception as e:
            # 如果失敗，降級使用內建截圖
            tab.get_screenshot(path=filepath, full_page=True)
