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
            EC.visibility_of_element_located(ProviderHomepageLocators.HEADER)
        )
        return True

    def goto_my_dashboard(self) -> MyDashboardPage:
        """Click the 'My dashboard' card, handling any Joyride tour overlays."""
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        import time

        # Try to dismiss Joyride tour overlay if present
        try:
            # Look for Joyride skip/close button
            skip_button = self.wait_with_timeout(2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Skip') or contains(text(), 'Skip') or @data-action='skip']"))
            )
            skip_button.click()
            time.sleep(0.5)
        except (TimeoutException, NoSuchElementException):
            # No Joyride tour present, or couldn't find skip button - continue anyway
            pass

        # Click the 'My Dashboard' card
        card = self.wait.until(
            EC.element_to_be_clickable(ProviderHomepageLocators.CARD_MY_DASH)
        )
        # Use JavaScript click to bypass any remaining overlays
        self.driver.execute_script("arguments[0].click();", card)
        return MyDashboardPage(self.driver)

    def goto_organizations(self) -> "OrganizationsPage":
        """Click the 'Organizations' card."""
        self.wait.until(
            EC.element_to_be_clickable(ProviderHomepageLocators.CARD_ORGANIZATIONS)
        ).click()
        return OrganizationsPage(self.driver)
