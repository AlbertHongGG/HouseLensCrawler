import re
from typing import Dict, Tuple

def parse_floor(text: str) -> Tuple[str, str]:
    """e.g., '2樓/共5樓' -> floor='2樓', total_floors='5樓'"""
    floor, total_floors = "", ""
    if not text or not isinstance(text, str):
        return floor, total_floors
    
    parts = text.split('/')
    if len(parts) == 2:
        floor = parts[0].strip()
        total_floors = parts[1].replace('共', '').strip()
    else:
        floor = text.strip()
    return floor, total_floors

def parse_layout(text: str) -> Dict[str, int]:
    """e.g., '3房2廳2衛' -> {'rooms': 3, 'living_rooms': 2, ...}"""
    layout = {"rooms": 0, "living_rooms": 0, "bathrooms": 0, "kitchens": 0, "balconies": 0}
    if not text or not isinstance(text, str):
        return layout
    
    patterns = {
        "rooms": r'(\d+)\s*房',
        "living_rooms": r'(\d+)\s*廳',
        "bathrooms": r'(\d+)\s*衛',
        "kitchens": r'(\d+)\s*(?:廚|室)',
        "balconies": r'(\d+)\s*陽台'
    }
    for k, p in patterns.items():
        m = re.search(p, text)
        if m:
            val = m.group(1) if m.group(1) else m.group(2)
            if val:
                layout[k] = int(val)
    return layout
