# pages/provider/organizations_page.py

from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class OrganizationsPage(BasePage):
    """POM for the Organizations list under /dashboard."""

    def is_loaded(self) -> bool:
        return self.find((By.XPATH, "//h1[text()='Organizations']")).is_displayed()
