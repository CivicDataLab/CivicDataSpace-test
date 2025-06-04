# pages/consumer/about_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.consumer.about_locators import AboutLocators

class AboutPage(BasePage):
    """Interactions on the About Us tab / page."""

    def is_heading_visible(self) -> bool:
        """Wait for the About Us heading to be visible."""
        return self.find((By.XPATH, AboutLocators.HEADING)).is_displayed()

    def is_paragraph_visible(self) -> bool:
        """Wait for the About Us paragraph to be visible."""
        return self.find((By.XPATH, AboutLocators.PARAGRAPH)).is_displayed()
