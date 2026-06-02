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
        from pages.provider.create_dataset_page import CreateDatasetPage
        from locators.provider.create_dataset_locators import CreateDatasetLocators

        # Wait for navigation to the dataset page
        self.wait_with_timeout(15).until(
            lambda d: '/dataset' in d.current_url
        )

        # Locate and JS-click the button
        btn = self.wait_with_timeout(15).until(
            EC.presence_of_element_located(OrgLocators.ADD_NEW_DATASET_BTN),
            message="Timed out waiting for the 'Add New Dataset' button"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for the type-selection modal
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.MODAL_TITLE)),
            message="Timed out waiting for 'Create New Dataset' modal to appear"
        )

        # Select "Data Dataset"
        data_dataset_card = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DATA_DATASET_CARD)),
            message="Timed out waiting for 'Data Dataset' option to be clickable"
        )
        data_dataset_card.click()

        # Confirm with "Create Dataset"
        create_btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.CREATE_DATASET_BUTTON)),
            message="Timed out waiting for 'Create Dataset' button to be clickable"
        )
        create_btn.click()

        # Wait for metadata tab
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

        # Wait for and JS-click the UseCases navigation link
        usecases_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.USECASES_NAV_LINK),
            message="Timed out waiting for the 'UseCases' link to be clickable"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", usecases_link)
        self.driver.execute_script("arguments[0].click();", usecases_link)

        # Wait for navigation to usecases URL
        self.wait_with_timeout(15).until(
            lambda d: '/usecases' in d.current_url
        )

        self.wait_with_timeout(15).until(
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for UseCases page to load"
        )

        return UseCasesListPage(self.driver)

    def click_collaboratives_card(self):
        """
        Click the Collaboratives navigation link in the organization dashboard.

        The organization dashboard has the same sidebar navigation as MyDashboard,
        so this works identically.

        Returns a CollaborativesListPage instance.
        """
        from pages.provider.collaboratives_list_page import CollaborativesListPage
        from locators.provider.collaboratives_list_page_locators import CollaborativesListPageLocators
        import time

        # Wait for and click the Collaboratives navigation link
        collaboratives_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(OrgLocators.COLLABORATIVES_NAV_LINK),
            message="Timed out waiting for the 'Collaboratives' link to be clickable"
        )

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", collaboratives_link)
        collaboratives_link.click()

        # Give the page time to navigate
        time.sleep(2)

        # Wait for the Collaboratives page to load — try multiple indicators for resilience
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.by import By
        loaded = False
        for locator in [
            CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON,
            (By.XPATH, "//span[contains(normalize-space(),'Collaborative')]"),
            (By.XPATH, "//*[contains(normalize-space(),'Collaborative')]"),
        ]:
            try:
                self.wait_with_timeout(20).until(EC.visibility_of_element_located(locator))
                loaded = True
                break
            except TimeoutException:
                continue

        if not loaded:
            raise TimeoutException("Timed out waiting for Collaboratives page to load")

        return CollaborativesListPage(self.driver)

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
