import re
from typing import Dict, Tuple, Any, Optional

def parse_int(val: Any) -> Optional[int]:
    """Helper function to parse an integer from a string."""
    if not val:
        return None
    if isinstance(val, int):
        return val
    s = str(val).replace(',', '')
    match = re.search(r'\d+', s)
    try:
        return int(match.group()) if match else None
    except ValueError:
        return None

def parse_float(val: Any) -> Optional[float]:
    """Helper function to parse a float from a string."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(',', '')
    match = re.search(r'[\d.]+', s)
    try:
        return float(match.group()) if match else None
    except ValueError:
        return None


