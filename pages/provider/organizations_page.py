# pages/provider/organizations_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from pages.base_page import BasePage
from locators.provider.org_locators import OrgLocators

class OrganizationsPage(BasePage):
    """POM for the Organizations list under /dashboard/organization."""

    def is_loaded(self) -> bool:
        """Check if the Organizations page is loaded."""
        return self.find((By.XPATH, "//h1[text()='Organizations']")).is_displayed()

    def select_org(self) -> "OrganizationsPage":
        """
        Select the test organization to access its dashboard.

        After clicking, the page redirects to:
        /dashboard/organization/my-test-agency/dataset

        This loads a dashboard identical to MyDashboard, with the Datasets
        section already visible.
        """
        # Click the organization card
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.ORG_TEST),
            message="Timed out waiting for the 'my test agency' org card to be clickable"
        ).click()

        # Wait for the organization dashboard to load by checking for the Drafts tab
        # This confirms we've navigated to the dataset page
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(OrgLocators.DRAFTS_TAB),
            message="Timed out waiting for organization dashboard to load (Drafts tab)"
        )

        return self

    def click_add_new_dataset(self):
        """
        Click the "Add New Dataset" button in the organization dashboard.

        Since select_org() already loads the datasets page, this button
        should be immediately visible.

        Returns a CreateDatasetPage instance.
        """
        from pages.provider.create_dataset_page import CreateDatasetPage

        # The Drafts tab should already be visible from select_org()
        # But we double-check to ensure the page is fully loaded
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(OrgLocators.DRAFTS_TAB),
            message="Timed out waiting for the 'Drafts' tab to appear"
        )

        # Wait for "Add New Dataset" button to be clickable
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.ADD_NEW_DATASET_BTN),
            message="Timed out waiting for the 'Add New Dataset' button to become clickable"
        )

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        ActionChains(self.driver).move_to_element(btn).click().perform()

        return CreateDatasetPage(self.driver)

    def click_usecases_card(self):
        """
        Click the UseCases navigation link in the organization dashboard.

        The organization dashboard has the same sidebar navigation as MyDashboard,
        so this works identically.

        Returns a UseCasesListPage instance.
        """
        from pages.provider.usecases_list_page import UseCasesListPage

        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.USECASES_NAV_LINK),
            message="Timed out waiting for the 'UseCases' link to be clickable"
        ).click()

        return UseCasesListPage(self.driver)

    def click_profile_card(self):
        """
        Click the Profile navigation link in the organization dashboard.

        The organization dashboard has the same sidebar navigation as MyDashboard,
        so this works identically.

        Returns an UpdateProfilePage instance.
        """
        from pages.provider.update_profile_page import UpdateProfilePage

        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.PROFILE_NAV_LINK),
            message="Timed out waiting for the 'Profile' link to be clickable"
        ).click()

        return UpdateProfilePage(self.driver)
