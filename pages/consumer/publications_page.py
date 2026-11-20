# pages/consumer/publications_page.py

from selenium.webdriver.support import expected_conditions as EC

from locators.consumer.publications_locators import PublicationsLocators as L
from pages.base_page import BasePage


class PublicationsPage(BasePage):
    """Public /publications listing and /publications/<slug> detail pages."""

    def load_listing(self, base_url: str, timeout: int = 30) -> "PublicationsPage":
        self.visit(f"{base_url.rstrip('/')}/publications")
        self.wait_with_timeout(timeout).until(
            EC.presence_of_element_located(L.CARD_LINK), message="/publications rendered no publication cards")
        return self

    def card_hrefs(self) -> set[str]:
        return {a.get_attribute("href") for a in self.driver.find_elements(*L.CARD_LINK)}

    def open_publication(self, url_slug: str, base_url: str, timeout: int = 30) -> "PublicationsPage":
        self.visit(f"{base_url.rstrip('/')}/publications/{url_slug}")
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(L.DETAIL_TITLE), message="The publication page never showed its title")
        return self

    def title(self) -> str:
        return self.find(L.DETAIL_TITLE).text.strip()

    def file_items(self) -> int:
        return len(self.driver.find_elements(*L.FILES_SECTION_ITEM))
