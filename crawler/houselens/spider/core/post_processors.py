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
    Calculates indoor_ping by summing main_building_ping and accessory_ping if both exist.
    Also assigns the visual highlight element to main_building_ping.
    """
    def process(self, data: Dict[str, Any], elements: Dict[str, ChromiumElement]) -> None:
        if 'indoor_ping' not in data or not data['indoor_ping']:
            mb = data.get('main_building_ping')
            ab = data.get('accessory_ping')
            if mb is not None and ab is not None:
                data['indoor_ping'] = round(mb + ab, 2)
                if 'main_building_ping' in elements:
                    elements['indoor_ping'] = elements['main_building_ping']
