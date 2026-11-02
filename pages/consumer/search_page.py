# pages/consumer/search_page.py
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from locators.consumer.search_locators import SearchLocators
from pages.base_page import BasePage

SEARCH_PATH = "/search"


class SearchPage(BasePage):
    """Interactions on the unified search page (/search)."""

    def load(self, base_url: str, query_string: str = ""):
        suffix = f"?{query_string}" if query_string else ""
        self.visit(f"{base_url.rstrip('/')}{SEARCH_PATH}{suffix}")
        return self

    def shows_unable_to_load_message(self, timeout: int = 20) -> bool:
        """Wait up to `timeout` seconds for the friendly error state.

        Before DataSpaceFrontend#511, a failed search call never updates
        this far: the page is left showing its "Loading" placeholder
        forever (the error is set but never read), so this times out
        instead of finding the message.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(SearchLocators.UNABLE_TO_LOAD_MESSAGE)
            )
            return True
        except Exception:
            return False
