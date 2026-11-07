# pages/consumer/collaboratives_page.py

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.consumer.collaboratives_locators import CollaborativesLocators


class CollaborativesPage(BasePage):
    """Public /collaboratives listing page."""

    def load(self, base_url: str, timeout: int = 20) -> "CollaborativesPage":
        # The grid renders client-side after the header images, so wait on a
        # card image specifically rather than any <img>.
        self.visit(f"{base_url.rstrip('/')}/collaboratives")
        try:
            self.wait_with_timeout(timeout).until(
                EC.presence_of_element_located(CollaborativesLocators.CARD_IMAGE)
            )
        except TimeoutException:
            pass  # let the test's own assertions report what's missing
        return self

    def list_image_srcs(self):
        """All <img> elements currently on the page."""
        return self.driver.find_elements(*CollaborativesLocators.IMAGE)
