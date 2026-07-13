import threading
import logging
from DrissionPage import ChromiumPage, ChromiumOptions
from ..config import AppConfig

class BrowserManager:
    """
    Manages browser instances per-thread using thread-local storage,
    but also globally tracks all active browsers to allow forceful cleanup.
    """
    def __init__(self):
        self._local = threading.local()
        self._lock = threading.Lock()
        self._active_browsers = []

    def get_browser(self) -> ChromiumPage:
        """
        Retrieves or creates a ChromiumPage for the current thread.
        """
        if not hasattr(self._local, 'browser') or self._local.browser is None:
            logging.info(f"[{threading.current_thread().name}] Initializing new ChromiumPage...")
            opts = ChromiumOptions()
            opts.headless(AppConfig.BROWSER_HEADLESS)
            page = ChromiumPage(opts)
            if not AppConfig.BROWSER_HEADLESS:
                try:
                    page.set.window.max()
                except Exception as e:
                    logging.warning(f"Failed to maximize window: {e}")
            self._local.browser = page
            
            with self._lock:
                self._active_browsers.append(page)
                
        return self._local.browser

    def close_current_browser(self):
        """
        Closes the browser instance for the current thread if it exists.
        """
        if hasattr(self._local, 'browser') and self._local.browser:
            browser = self._local.browser
            try:
                browser.quit()
            except Exception as e:
                logging.debug(f"Error closing browser in thread: {e}")
            
            with self._lock:
                if browser in self._active_browsers:
                    self._active_browsers.remove(browser)
            
            self._local.browser = None

    def close_all(self):
        """
        Forcefully closes ALL tracked browsers. 
        Used during graceful shutdown to prevent zombie processes.
        """
        with self._lock:
            count = len(self._active_browsers)
            if count > 0:
                logging.info(f"[BrowserManager] Force closing {count} active browsers...")
                for browser in self._active_browsers:
                    try:
                        browser.quit()
                    except Exception as e:
                        logging.debug(f"Error forcefully closing browser: {e}")
                self._active_browsers.clear()

# Global singleton instance
browser_manager = BrowserManager()
