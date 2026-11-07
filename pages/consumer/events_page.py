# pages/consumer/events_page.py

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.consumer.events_locators import EventsLocators


class EventsPage(BasePage):
    """Public /events listing and /events/<slug> detail pages."""

    def load_listing(self, base_url: str, timeout: int = 20) -> "EventsPage":
        self.visit(f"{base_url.rstrip('/')}/events")
        try:
            self.wait_with_timeout(timeout).until(
                EC.visibility_of_element_located(EventsLocators.LISTING_HEADER)
            )
        except TimeoutException:
            pass  # let the test's own assertions report what's missing
        return self

    def card_links(self):
        """<a> elements on the listing that link into an event detail page."""
        return self.driver.find_elements(*EventsLocators.CARD_LINK)

    def open_event(self, url_slug: str, base_url: str, timeout: int = 20) -> "EventsPage":
        self.visit(f"{base_url.rstrip('/')}/events/{url_slug}")
        try:
            self.wait_with_timeout(timeout).until(
                EC.visibility_of_element_located(EventsLocators.DETAIL_HEADER)
            )
        except TimeoutException:
            pass
        return self

    def detail_header_text(self) -> str:
        return self.find(EventsLocators.DETAIL_HEADER).text

    def has_luma_iframe(self) -> bool:
        return len(self.driver.find_elements(*EventsLocators.LUMA_IFRAME)) > 0

    def luma_iframe_src(self):
        elems = self.driver.find_elements(*EventsLocators.LUMA_IFRAME)
        return elems[0].get_attribute("src") if elems else None
