from enum import Enum
from collections import defaultdict
from typing import Callable, Dict, List, Any

class Event(Enum):
    """
    系統生命週期事件定義
    """
    SPIDER_STARTED = "SPIDER_STARTED"           # 爬蟲啟動
    ELEMENTS_LOCATED = "ELEMENTS_LOCATED"       # DOM 元素定位完成 (kwargs: tab, elements, source_id, platform_name)
    ITEM_PARSED = "ITEM_PARSED"                 # 屬性資料解析完成 (kwargs: item)
    COMMUNITY_PARSED = "COMMUNITY_PARSED"       # 社區資料解析完成 (kwargs: community)
    SPIDER_FINISHED = "SPIDER_FINISHED"         # 爬蟲結束
    DUPLICATE_DETECTED = "DUPLICATE_DETECTED"   # 發現重複物件 (kwargs: platform, source_id, url_a, url_b)

class EventBus:
    """
    事件匯流排：負責註冊監聽器與廣播事件
    採用 Singleton 模式確保全域只有一個匯流排
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.listeners = defaultdict(list)
        return cls._instance

    def subscribe(self, event: Event, listener: Callable):
        """註冊事件監聽器"""
        self.listeners[event].append(listener)

    def emit(self, event: Event, **kwargs):
        """廣播事件給所有監聽器"""
        for listener in self.listeners.get(event, []):
            try:
                listener(**kwargs)
            except Exception as e:
                import logging
                logging.error(f"[EventBus] Error in listener {listener.__name__} for event {event}: {e}")

# 全域單一實例
event_bus = EventBus()
