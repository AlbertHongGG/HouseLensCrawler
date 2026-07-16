import os
from dotenv import load_dotenv

load_dotenv()

from enum import Enum

class CrawlMode(str, Enum):
    FULL = "full"
    TARGETED = "targeted"
    CONSUMER = "consumer"

class SpiderConfig:
    """
    Holds configuration limits for a specific spider, read from the environment.
    """
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        
        prefix = f"SPIDER_{platform_name.upper()}"
        self.max_items = int(os.environ.get(f"{prefix}_MAX_ITEMS", "1000"))
        self.max_pages = int(os.environ.get(f"{prefix}_MAX_PAGES", "10"))
        self.start_url = os.environ.get(f"{prefix}_START_URL", "")
        
        target_urls_str = os.environ.get(f"{prefix}_TARGET_URLS", "")
        self.target_urls = [s.strip() for s in target_urls_str.split(",") if s.strip()]

class AppConfig:
    """
    Global application configuration loaded from environment variables.
    """
    _active_str = os.environ.get("ACTIVE_SPIDERS", "")
    ACTIVE_SPIDERS = [s.strip() for s in _active_str.split(",") if s.strip()]

    CRAWL_MODE = CrawlMode(os.environ.get("CRAWL_MODE", "full").lower())

    STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "json").lower()
    JSON_STORAGE_PATH = os.environ.get("JSON_STORAGE_PATH", "data")
    ENABLE_VISUAL_VERIFICATION = os.environ.get("ENABLE_VISUAL_VERIFICATION", "False").lower() == "true"
    ENGINE_MAX_WORKERS = int(os.environ.get("ENGINE_MAX_WORKERS", "3"))
    BROWSER_HEADLESS = os.environ.get("BROWSER_HEADLESS", "True").lower() == "true"
    BROWSER_REUSE_INSTANCE = os.environ.get("BROWSER_REUSE_INSTANCE", "True").lower() == "true"

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
