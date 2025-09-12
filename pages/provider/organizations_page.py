# pages/provider/organizations_page.py

from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from selenium.webdriver.support.ui import WebDriverWait
from locators.provider.org_locators import OrgLocators

class OrganizationsPage(BasePage):
    """POM for the Organizations list under /dashboard."""

    def is_loaded(self) -> bool:
        return self.find((By.XPATH, "//h1[text()='Organizations']")).is_displayed()

    def select_org(self) -> bool:
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, ORGLocators.ORG_TEST)),
            message="Timed out waiting for the 'ORG Dashboard' card to be clickable"
        ).click()
        return self
