import logging
from .base import BaseExtension
from ..engine.events import EventBus, Event
from ..models.property import StandardProperty
from ..storage.interfaces import IQueueStorage

class CrawlQueueExtension(BaseExtension):
    """
    Listens to ITEM_PARSED event. 
    If the property contains a community_url, pushes it into the queue.
    """
    def __init__(self, queue_storage: IQueueStorage):
        self.queue_storage = queue_storage

    def setup(self, bus: EventBus):
        bus.subscribe(Event.ITEM_PARSED, self.on_item_parsed)
        logging.info(f"[Extension] CrawlQueueExtension registered.")

    def on_item_parsed(self, item: StandardProperty, **kwargs):
        community_url = getattr(item, 'community_url', None)
        if not community_url:
            return

        # Determine the spider name based on the platform
        spider_name = f"{item.source_platform}_community"

        try:
            success = self.queue_storage.push_job(spider_name, community_url)
            if success:
                logging.info(f"[QueueExtension] Pushed community to queue: {community_url}")
        except Exception as e:
            logging.error(f"[QueueExtension] Error pushing to queue: {e}")
