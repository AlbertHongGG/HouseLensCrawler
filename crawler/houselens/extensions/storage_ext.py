import logging
from .base import BaseExtension
from ..engine.events import EventBus, Event
from ..models.property import StandardProperty
from ..engine.semantic_dedup import RuleBasedScorer

class StorageExtension(BaseExtension):
    """
    資料儲存外掛 (Extension)。
    主動監聽 `ITEM_PARSED` 事件，將清洗完畢的資料儲存至指定媒介 (JSONL, DB等)。
    """
    def __init__(self, storage_strategy):
        self.storage_strategy = storage_strategy
        self.bus = None

    def setup(self, bus: EventBus):
        self.bus = bus
        self.bus.subscribe(Event.ITEM_PARSED, self.on_item_parsed)
        self.bus.subscribe(Event.COMMUNITY_PARSED, self.on_community_parsed)
        logging.info(f"[Extension] StorageExtension registered with {self.storage_strategy.__class__.__name__}.")

    def on_item_parsed(self, item: StandardProperty, **kwargs):
        """事件處理常式：當 Spider 解析出 StandardProperty 時寫入儲存體"""
        try:
            # Semantic Deduplication Hook
            if hasattr(self.storage_strategy, 'find_potential_duplicates'):
                candidates = self.storage_strategy.find_potential_duplicates(item)
                if candidates:
                    best_match, score = RuleBasedScorer.evaluate(item, candidates)
                    if score >= 90 and best_match:
                        # 觸發系統事件 (讓 DuplicateLoggerExtension 接手處理紀錄)
                        self.bus.emit(Event.DUPLICATE_DETECTED, 
                            platform=item.source_platform, 
                            source_id=item.source_id, 
                            url_a=item.url, 
                            url_b=best_match.url if best_match.url else best_match.property_uuid
                        )
                        return

            self.storage_strategy.save(item)
            logging.info(f"[{item.source_platform}] Saved property {item.source_id}.")
        except Exception as e:
            logging.error(f"[StorageExtension] Failed to process/save item {item.source_id}: {e}")

    def on_community_parsed(self, community, **kwargs):
        """事件處理常式：當 Spider 解析出 StandardCommunity 時寫入儲存體"""
        try:
            self.storage_strategy.save_community(community)
            logging.info(f"[{community.source_platform}] Saved community {community.source_id}.")
        except Exception as e:
            logging.error(f"[StorageExtension] Failed to save community {community.source_id}: {e}")
