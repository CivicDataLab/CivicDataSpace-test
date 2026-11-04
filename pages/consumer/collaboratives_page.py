# pages/consumer/collaboratives_page.py

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.consumer.collaboratives_locators import CollaborativesLocators

# The grid fetches its data client-side (useQuery); the header/hero images
# are in the initial HTML well before the cards exist, so waiting on "any
# <img>" (or a short fixed sleep) returns before the cards render. Wait on a
# card image specifically — they're all served from the storage CDN.
CARD_IMAGE = (By.XPATH, "//img[contains(@src,'cloudfront') or contains(@src,'/dev/public/')]")


class CollaborativesPage(BasePage):
    """Public /collaboratives listing page."""

    def load(self, base_url: str, timeout: int = 20) -> "CollaborativesPage":
        self.visit(f"{base_url.rstrip('/')}/collaboratives")
        try:
            self.wait_with_timeout(timeout).until(
                EC.presence_of_element_located(CARD_IMAGE)
            )
        except TimeoutException:
            pass  # let the test's own assertions report what's missing
        return self

    def has_image_with_src(self, src: str) -> bool:
        """True if some <img> on the page currently resolves to exactly *src*."""
        try:
            self.driver.find_element(*CollaborativesLocators.img_with_src(src))
            return True
        except NoSuchElementException:
            return False

    def list_image_srcs(self):
        """All <img> elements currently on the page."""
        return self.driver.find_elements(By.TAG_NAME, "img")
