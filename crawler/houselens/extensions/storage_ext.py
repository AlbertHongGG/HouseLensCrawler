import logging
from .base import BaseExtension
from ..engine.events import EventBus, Event
from ..models.property import StandardProperty

class StorageExtension(BaseExtension):
    """
    資料儲存外掛 (Extension)。
    主動監聽 `ITEM_PARSED` 事件，將清洗完畢的資料儲存至指定媒介 (JSONL, DB等)。
    """
    def __init__(self, storage_strategy):
        self.storage_strategy = storage_strategy

    def setup(self, bus: EventBus):
        bus.subscribe(Event.ITEM_PARSED, self.on_item_parsed)
        bus.subscribe(Event.COMMUNITY_PARSED, self.on_community_parsed)
        logging.info(f"[Extension] StorageExtension registered with {self.storage_strategy.__class__.__name__}.")

    def on_item_parsed(self, item: StandardProperty, **kwargs):
        """事件處理常式：當 Spider 解析出 StandardProperty 時寫入儲存體"""
        try:
            self.storage_strategy.save(item)
            logging.info(f"[{item.source_platform}] Saved property {item.source_id}.")
        except Exception as e:
            logging.error(f"[StorageExtension] Failed to save item {item.source_id}: {e}")

    def on_community_parsed(self, community, **kwargs):
        """事件處理常式：當 Spider 解析出 StandardCommunity 時寫入儲存體"""
        try:
            self.storage_strategy.save_community(community)
            logging.info(f"[{community.source_platform}] Saved community {community.source_id}.")
        except Exception as e:
            logging.error(f"[StorageExtension] Failed to save community {community.source_id}: {e}")
