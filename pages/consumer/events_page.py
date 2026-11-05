# pages/consumer/events_page.py
from urllib.parse import urljoin

from locators.consumer.events_locators import EventDetailLocators, EventsLocators
from pages.base_page import BasePage

EVENTS_PATH = "/events"


class EventsPage(BasePage):
    """Interactions on the public events listing page (/events)."""

    def load(self, base_url: str):
        self.visit(f"{base_url.rstrip('/')}{EVENTS_PATH}")
        return self

    def heading_text(self) -> str:
        return self.find(EventsLocators.HEADING).text.strip()

    def current_path(self) -> str:
        return self.driver.current_url

    def event_card_hrefs(self) -> list[str]:
        """Absolute hrefs of every rendered event card, in listing order."""
        try:
            links = self.finds(EventsLocators.EVENT_CARD_LINKS)
        except Exception:
            return []
        return [el.get_attribute("href") for el in links if el.get_attribute("href")]


class EventDetailPage(BasePage):
    """Interactions on a single event's detail page (/events/<slug>)."""

    def load_href(self, href: str, base_url: str):
        self.visit(urljoin(base_url, href))
        return self

    def heading_text(self) -> str:
        return self.find(EventDetailLocators.HEADING).text.strip()

    def current_path(self) -> str:
        return self.driver.current_url
