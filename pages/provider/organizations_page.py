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
        Click the "Add New Dataset" button in the organization dashboard,
        handle the dataset type selection modal, and proceed to dataset creation.

        Since select_org() already loads the datasets page, this button
        should be immediately visible.

        Flow:
        1. Click "Add New Dataset" button
        2. Wait for modal to appear
        3. Select "Data Dataset" option
        4. Click "Create Dataset" to proceed
        5. Return CreateDatasetPage instance

        Returns a CreateDatasetPage instance.
        """
        from pages.provider.create_dataset_page import CreateDatasetPage
        from locators.provider.create_dataset_locators import CreateDatasetLocators

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

        # Wait for the "Create New Dataset" modal to appear
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.MODAL_TITLE)),
            message="Timed out waiting for 'Create New Dataset' modal to appear"
        )

        # Click the "Data Dataset" card option
        data_dataset_card = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DATA_DATASET_CARD)),
            message="Timed out waiting for 'Data Dataset' option to be clickable"
        )
        data_dataset_card.click()

        # Click the "Create Dataset" button to proceed
        create_btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.CREATE_DATASET_BUTTON)),
            message="Timed out waiting for 'Create Dataset' button to be clickable"
        )
        create_btn.click()

        # Wait for the metadata tab to appear (confirms we're in the dataset creation form)
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.TAB_METADATA)),
            message="Timed out waiting for Metadata tab to appear after creating dataset"
        )

        return CreateDatasetPage(self.driver)

    def click_usecases_card(self):
        """
        Click the UseCases navigation link in the organization dashboard.

        The organization dashboard has the same sidebar navigation as MyDashboard,
        so this works identically.

        Returns a UseCasesListPage instance.
        """
        from pages.provider.usecases_list_page import UseCasesListPage
        from locators.provider.usecases_list_page_locators import UseCaseListPageLocators
        import time

        # Wait for and click the UseCases navigation link
        usecases_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.USECASES_NAV_LINK),
            message="Timed out waiting for the 'UseCases' link to be clickable"
        )

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", usecases_link)
        usecases_link.click()

        # Give the page time to navigate
        time.sleep(2)

        # Wait for the UseCases page to load by checking for the "Add New UseCase" button
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for UseCases page to load"
        )

        return UseCasesListPage(self.driver)

    def click_profile_card(self):
        """
        Click the Profile navigation link in the organization dashboard.

        The organization dashboard has the same sidebar navigation as MyDashboard,
        so this works identically.

        Returns an UpdateProfilePage instance.
        """
        from pages.provider.update_profile_page import UpdateProfilePage
        from locators.provider.update_profile_locators import UpdateProfilePageLocators
        import time

        # Wait for and click the Profile navigation link
        profile_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.PROFILE_NAV_LINK),
            message="Timed out waiting for the 'Profile' link to be clickable"
        )

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", profile_link)
        profile_link.click()

        # Give the page time to navigate
        time.sleep(2)

        # Wait for the organization profile page to load
        # Organization profiles don't have "My Profile" heading - wait for Save button instead
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located((By.XPATH, "//button[normalize-space()='Save']")),
            message="Timed out waiting for Organization Profile page to load"
        )

        return UpdateProfilePage(self.driver)
