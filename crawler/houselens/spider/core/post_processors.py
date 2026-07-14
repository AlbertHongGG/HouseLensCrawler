import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from DrissionPage.items import ChromiumElement

class BasePostProcessor(ABC):
    """
    Abstract base class for all post-processors.
    Post-processors run after all extraction rules have completed,
    allowing for derived field calculations (e.g., indoor_ping = main_building_ping + accessory_ping).
    """
    @abstractmethod
    def process(self, data: Dict[str, Any], elements: Dict[str, ChromiumElement]) -> None:
        pass

class CalculateIndoorPingProcessor(BasePostProcessor):
    """
    Calculates indoor_ping by summing main_building_ping, balcony_ping, and rain_cover_ping.
    It will only calculate if at least balcony or rain_cover exists.
    """
    def process(self, data: Dict[str, Any], elements: Dict[str, ChromiumElement]) -> None:
        if 'indoor_ping' not in data or not data['indoor_ping']:
            mb = data.get('main_building_ping')
            if mb is not None:
                ab = data.get('accessory_ping')
                if ab is not None:
                    data['indoor_ping'] = round(mb + ab, 2)
                else:
                    ab1 = data.get('balcony_ping')
                    ab2 = data.get('rain_cover_ping')
                    if ab1 is not None or ab2 is not None:
                        total_ab = (ab1 or 0) + (ab2 or 0)
                        data['indoor_ping'] = round(mb + total_ab, 2)
