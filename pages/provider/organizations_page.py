# pages/provider/organizations_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from pages.base_page import BasePage
from locators.provider.org_locators import OrgLocators

class OrganizationsPage(BasePage):
    """POM for the Organizations list under /dashboard."""

    def is_loaded(self) -> bool:
        return self.find((By.XPATH, "//h1[text()='Organizations']")).is_displayed()

    def select_org(self) -> "OrganizationsPage":
        """Select the test organization to access its dashboard."""
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, OrgLocators.ORG_TEST)),
            message="Timed out waiting for the 'ORG Dashboard' card to be clickable"
        ).click()
        return self

    def click_add_new_dataset(self):
        """
        Click the "Add New Dataset" button in the organization dashboard.
        Returns a CreateDatasetPage instance.
        """
        from pages.provider.create_dataset_page import CreateDatasetPage

        # Wait for the "Drafts" tab to appear
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, OrgLocators.DRAFTS_TAB)),
            message="Timed out waiting for the 'Drafts' tab to appear"
        )

        # Wait for "Add New Dataset" button to be clickable
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, OrgLocators.ADD_NEW_DATASET_BTN)),
            message="Timed out waiting for the 'Add New Dataset' button to become clickable"
        )

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        ActionChains(self.driver).move_to_element(btn).click().perform()

        return CreateDatasetPage(self.driver)

    def click_usecases_card(self):
        """
        Click the UseCases navigation link in the organization dashboard.
        Returns a UseCasesListPage instance.
        """
        from pages.provider.usecases_list_page import UseCasesListPage

        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, OrgLocators.USECASES_NAV_LINK)),
            message="Timed out waiting for the 'UseCases' link to be clickable"
        ).click()
        return UseCasesListPage(self.driver)

    def click_profile_card(self):
        """
        Click the Profile navigation link in the organization dashboard.
        Returns an UpdateProfilePage instance.
        """
        from pages.provider.update_profile_page import UpdateProfilePage

        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, OrgLocators.PROFILE_NAV_LINK)),
            message="Timed out waiting for the 'Profile' link to be clickable"
        ).click()
        return UpdateProfilePage(self.driver)
