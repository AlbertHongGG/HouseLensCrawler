import threading
import logging
from DrissionPage import ChromiumPage, ChromiumOptions
from ..config import AppConfig

class BrowserPool:
    """
    Manages browser instances per-thread using thread-local storage.
    Ensures that each worker thread gets exactly one isolated browser instance.
    """
    def __init__(self):
        self._local = threading.local()

    def get_browser(self) -> ChromiumPage:
        """
        Retrieves or creates a ChromiumPage for the current thread.
        """
        if not hasattr(self._local, 'browser'):
            logging.info(f"[{threading.current_thread().name}] Initializing new ChromiumPage...")
            opts = ChromiumOptions()
            opts.headless(AppConfig.BROWSER_HEADLESS)
            page = ChromiumPage(opts)
            if not AppConfig.BROWSER_HEADLESS:
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    width = user32.GetSystemMetrics(0)
                    height = user32.GetSystemMetrics(1)
                    page.set.window.size(width, height)
                    page.set.window.location(0, 0)
                except Exception as e:
                    logging.warning(f"Failed to set window size: {e}")
                    page.set.window.max()
            self._local.browser = page
            
        return self._local.browser

    def close_current_browser(self):
        """
        Closes the browser instance for the current thread if it exists.
        Because this uses threading.local(), it will ONLY close the browser 
        belonging to the worker thread that called this method. Other workers' 
        browsers remain completely unaffected.
        """
        if hasattr(self._local, 'browser'):
            self._local.browser.quit()
            del self._local.browser

# Global singleton instance
browser_pool = BrowserPool()
