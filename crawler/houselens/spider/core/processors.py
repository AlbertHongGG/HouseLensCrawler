import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Tuple

class BaseProcessor(ABC):
    """
    Base class for a data processor/transformer.
    Processors are used in a pipeline to clean and transform raw text data.
    """
    @abstractmethod
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        pass


class RemoveSpaces(BaseProcessor):
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        if isinstance(value, str):
            return value.replace(' ', '').replace('\n', '')
        return value


class ExtractFloat(BaseProcessor):
    """
    Extracts the first floating point number from a string.
    """
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if not value or not isinstance(value, str):
            return 0.0
        match = re.search(r'[\d,.]+', value)
        if match:
            clean_str = match.group().replace(',', '')
            # If it's just a dot or empty, return 0.0
            if clean_str == '.' or not clean_str:
                return 0.0
            try:
                return float(clean_str)
            except ValueError:
                return 0.0
        return 0.0


class ParseAge(BaseProcessor):
    """
    Extracts property age in years. Returns 0.0 for pre-sale (預售).
    """
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> float:
        if not value or not isinstance(value, str):
            return 0.0
        if "預售" in value or "預" in value:
            return 0.0
        
        match = re.search(r'([\d.]+)\s*(年|個月)', value)
        if match:
            num = float(match.group(1))
            unit = match.group(2)
            if unit == '個月':
                return round(num / 12, 1)
            return num
            
        # fallback to any float
        match = re.search(r'[\d.]+', value)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        return 0.0


class ParseLayout(BaseProcessor):
    """
    Parses a layout string (e.g. 3房2廳2衛) into a dictionary.
    """
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        layout = {
            'rooms': 0,
            'living_rooms': 0,
            'bathrooms': 0,
            'balconies': 0,
            'kitchens': 0
        }
        if not value or not isinstance(value, str):
            return layout
            
        patterns = {
            'rooms': r'(\d+)\s*房',
            'living_rooms': r'(\d+)\s*廳',
            'bathrooms': r'(\d+)\s*衛',
            'balconies': r'(\d+)\s*陽台',
            'kitchens': r'(\d+)\s*廚'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, value)
            if match:
                layout[key] = int(match.group(1))
        
        # If '開放空間' in value and no rooms parsed, could set specific flags if needed
        return layout


class ExtractAfterString(BaseProcessor):
    """
    Extracts text that appears after a specific marker string.
    """
    def __init__(self, marker: str):
        self.marker = marker
        
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> str:
        if not value or not isinstance(value, str):
            return ""
        if self.marker in value:
            return value.split(self.marker, 1)[1].strip()
        return value.strip()


class SplitProcessor(BaseProcessor):
    """
    Splits the string by a delimiter and returns the part at the specified index.
    """
    def __init__(self, delimiter: str = ':', index: int = 1):
        self.delimiter = delimiter
        self.index = index
        
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> str:
        if not value or not isinstance(value, str):
            return ""
        parts = value.split(self.delimiter)
        if len(parts) > self.index:
            return parts[self.index].strip()
        return value.strip()


class RegexProcessor(BaseProcessor):
    """
    Applies a regular expression and returns the matched group.
    """
    def __init__(self, pattern: str, group: int = 1):
        self.pattern = pattern
        self.group = group
        
    def process(self, value: Any, context: Optional[Dict[str, Any]] = None) -> str:
        if not value or not isinstance(value, str):
            return ""
        match = re.search(self.pattern, value)
        if match:
            try:
                return match.group(self.group).strip()
            except IndexError:
                return match.group(0).strip()
        return ""
