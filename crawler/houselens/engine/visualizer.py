import os
import logging
from DrissionPage import ChromiumPage
from typing import Any

class VisualVerificationService:
    """
    視覺化驗證引擎。
    專責處理網頁 DOM 元素的標註與整頁截圖，輔助開發者快速驗證萃取邏輯是否定位正確。
    符合 SRP 原則：不涉及資料萃取，只專注於畫面呈現與保存。
    """
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir

    def highlight_all(self, elements_dict: dict):
        """
        遍歷字典中所有的元素並標記對應的 Key (field_name)。
        """
        for field_name, ele in elements_dict.items():
            if ele:
                self.highlight(ele, field_name)

    def highlight(self, ele: Any, label: str):
        """
        在 DOM 元素上覆蓋視覺化標記 (紅框 + 標籤名稱)。
        透過 DrissionPage 的 run_js 注入，保證在各種 RWD 版面中定位精確且不跑版。
        
        Args:
            ele: 要標記的 ChromiumElement 物件
            label: 要顯示的參數名稱 (如 "total_price")
        """
        if not ele:
            return

        js_script = f"""
        let el = this;
        let text = '{label}';
        // 設定元素本身為相對定位，以確保 label 能以其為基準
        if (window.getComputedStyle(el).position === 'static') {{
            el.style.position = 'relative';
        }}
        // 繪製紅框
        el.style.border = '3px solid red';
        el.style.boxSizing = 'border-box';
        
        // 建立浮動 Label
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
        labelDiv.style.pointerEvents = 'none'; // 避免阻擋點擊
        
        el.appendChild(labelDiv);
        """
        try:
            # 讓 element 自身執行 JS (在內部 this 會指向該 element)
            ele.run_js(js_script)
        except Exception as e:
            logging.debug(f"[Visualizer] Failed to highlight {label}: {e}")

    def save_screenshot(self, tab: ChromiumPage, spider_name: str, filename: str):
        """
        對當前網頁拍攝整頁截圖 (Full-page screenshot)，並存放到指定爬蟲的資料夾。
        
        Args:
            tab: 當前操作的分頁
            spider_name: 爬蟲名稱 (如 "591")
            filename: 截圖檔案名稱 (如 "20165902.png")
        """
        target_dir = os.path.join(self.output_dir, spider_name)
        os.makedirs(target_dir, exist_ok=True)
        
        filepath = os.path.join(target_dir, filename)
        try:
            logging.info(f"[Visualizer] Capturing full page screenshot to {filepath}...")
            # 使用 DrissionPage 內建長截圖功能
            tab.get_screenshot(path=filepath, full_page=True)
            logging.info(f"[Visualizer] Screenshot saved: {filename}")
        except Exception as e:
            logging.error(f"[Visualizer] Failed to take screenshot {filename}: {e}")
