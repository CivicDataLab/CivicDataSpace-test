# pages/provider/provider_home_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage
from locators.provider.provider_homepage_locators import ProviderHomepageLocators
from pages.provider.organizations_page import OrganizationsPage
from pages.provider.my_dashboard_page import MyDashboardPage

class ProviderHomePage(BasePage):
    """POM for the post-login Provider ‘User Dashboard’ landing page."""

    def load(self):
        """(Optional) Navigate directly, if you ever want to skip login."""
        self.visit(ProviderHomepageLocators.URL)

    def is_header_visible(self) -> bool:
        # this waits for the actual dashboard header
        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, ProviderHomepageLocators.HEADER))
        )
        return True

    def goto_my_dashboard(self) -> MyDashboardPage:
        """Click the ‘My dashboard’ card."""
        self.wait.until(
            EC.element_to_be_clickable((By.XPATH, ProviderHomepageLocators.CARD_MY_DASH))
        ).click()
        return MyDashboardPage(self.driver)

    def goto_organizations(self) -> "OrganizationsPage":
        """Click the ‘Organizations’ card."""
        self.wait.until(
            EC.element_to_be_clickable((By.XPATH, ProviderHomepageLocators.CARD_ORGANIZATIONS))
        ).click()
        return OrganizationsPage(self.driver)
