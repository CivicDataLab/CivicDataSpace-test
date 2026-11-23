# pages/consumer/published_item_page.py
#
# Read-only view of a published item as an anonymous visitor: open a detail or
# listing URL, then report what the page shows. Assertions live in the tests.

import time
from urllib.parse import urlencode

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from locators.consumer.published_item_locators import PublishedItemLocators as L
from pages.base_page import BasePage

DETAIL_PATHS = {"dataset": "datasets", "usecase": "usecases", "collaborative": "collaboratives", "aimodel": "aimodels",
                "publication": "publications"}


class PublishedItemPage(BasePage):

    def text(self) -> str:
        return self.find(L.BODY).text

    def _wait_text(self, predicate, timeout):
        try:
            WebDriverWait(self.driver, timeout).until(lambda d: predicate(self.text()))
            return True
        except TimeoutException:
            return False

    def page_value(self, name, timeout=0):
        """A global the page's own scripts may have set, or None.

        With `timeout`, keep looking that long: handlers such as an image's
        onerror run a moment after the page shows its text.
        """
        read = lambda d: d.execute_script("return window[arguments[0]] ?? null;", name)
        try:
            return WebDriverWait(self.driver, timeout, poll_frequency=0.25).until(read) if timeout else read(self.driver)
        except TimeoutException:
            return None

    def open_detail(self, base_url, kind, key, expect_text, timeout=30):
        """Open /<kind>/<id-or-slug>; wait until `expect_text` or a not-found message shows."""
        self.visit(f"{base_url.rstrip('/')}/{DETAIL_PATHS[kind]}/{key}")
        self._wait_text(lambda t: expect_text in t or any(n in t for n in L.NOT_FOUND_TEXTS), timeout)
        return self

    def open_listing(self, base_url, path, timeout=30, **params):
        query = f"?{urlencode(params)}" if params else ""
        self.visit(f"{base_url.rstrip('/')}/{path}{query}")
        self._wait_text(lambda t: any(s in t for s in L.LISTING_SETTLED_TEXTS), timeout)
        return self

    def open_tab(self, name):
        tab = self.find((By.XPATH, L.TAB.format(name)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'})", tab)
        tab.click()
        return self

    def shows(self, text, timeout=10) -> bool:
        return self._wait_text(lambda t: text in t, timeout)

    def is_not_found(self) -> bool:
        return any(n in self.text() for n in L.NOT_FOUND_TEXTS)

    def aria_labels(self) -> list[str]:
        return [e.get_attribute("aria-label") for e in self.finds(L.LABELLED)]

    def external_links(self) -> list[str]:
        return [a.get_attribute("href") for a in self.driver.find_elements(*L.EXTERNAL_LINKS)]

    def listing_shows(self, base_url, path, text, present=True, attempts=4, **params) -> bool:
        """Reload the listing until `text` is (or is no longer) on it; search indexing lags a little."""
        for _ in range(attempts):
            self.open_listing(base_url, path, **params)
            if (text in self.text()) == present:
                return True
            time.sleep(5)
        return False
