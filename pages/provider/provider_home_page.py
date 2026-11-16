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

        # Dismiss the Joyride tour if it is showing (it is switched off in the frontend).
        try:
            for skip_button in self.present_now((By.XPATH, "//button[contains(@aria-label, 'Skip') or contains(text(), 'Skip') or @data-action='skip']")):
                skip_button.click()
                time.sleep(0.5)
                break
        except Exception:
            pass

        # Wait for the loading spinner to clear before looking for the card
        try:
            self.wait_with_timeout(30).until(
                self.gone((By.XPATH, "//*[normalize-space(text())='Loading']"))
            )
        except TimeoutException:
            pass

        card = self.wait_with_timeout(30).until(
            EC.element_to_be_clickable(ProviderHomepageLocators.CARD_MY_DASH)
        )
        self.driver.execute_script("arguments[0].click();", card)
        return MyDashboardPage(self.driver)

    def goto_organizations(self) -> "OrganizationsPage":
        """Click the 'Organizations' card."""
        from selenium.common.exceptions import TimeoutException

        # Wait for the loading spinner to clear before looking for the card
        try:
            self.wait_with_timeout(30).until(
                self.gone((By.XPATH, "//*[normalize-space(text())='Loading']"))
            )
        except TimeoutException:
            pass

        card = self.wait_with_timeout(30).until(
            EC.element_to_be_clickable(ProviderHomepageLocators.CARD_ORGANIZATIONS)
        )
        self.driver.execute_script("arguments[0].click();", card)
        return OrganizationsPage(self.driver)
