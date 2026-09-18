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

    # The page heading is no longer an <h1>Organizations</h1>; the reliable signal that the
    # org list has rendered is the presence of at least one org card link.
    ORG_CARD_ANY = (By.XPATH, "//a[contains(@href,'/dashboard/organization/')]")

    def is_loaded(self) -> bool:
        """Check if the Organizations page is loaded (an org card is present)."""
        return self.find(self.ORG_CARD_ANY).is_displayed()

    def select_org(self) -> "OrganizationsPage":
        """
        Select the test organization to access its dashboard.

        After clicking, the page redirects to:
        /dashboard/organization/my-test-agency/dataset

        This loads a dashboard identical to MyDashboard, with the Datasets
        section already visible.
        """
        # Wait for the org list page to finish rendering before looking for cards
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(self.ORG_CARD_ANY),
            message="Organizations list page did not load"
        )

        # Try the specific test org first; fall back to the first available org card
        org_el = None
        for locator in [
            OrgLocators.ORG_TEST,
            (By.XPATH, "//a[contains(@href,'/dashboard/organization/')]"),
        ]:
            try:
                org_el = self.wait_with_timeout(25).until(
                    EC.element_to_be_clickable(locator)
                )
                break
            except TimeoutException:
                continue

        if org_el is None:
            raise TimeoutException("Timed out waiting for the 'my test agency' org card to be clickable")

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", org_el)
        self.driver.execute_script("arguments[0].click();", org_el)

        # Wait for the organization dashboard to load by checking for the Drafts tab
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(OrgLocators.DRAFTS_TAB),
            message="Timed out waiting for organization dashboard to load (Drafts tab)"
        )

        return self

    def click_add_new_dataset(self):
        from locators.provider.create_dataset_locators import CreateDatasetLocators

        return self._create_dataset(
            OrgLocators.ADD_NEW_DATASET_BTN, CreateDatasetLocators.DATA_DATASET_CARD, "dataset"
        )

    def click_add_new_prompt_dataset(self):
        from locators.provider.create_dataset_locators import CreateDatasetLocators

        return self._create_dataset(
            OrgLocators.ADD_NEW_DATASET_BTN, CreateDatasetLocators.PROMPT_DATASET_CARD, "prompt dataset"
        )

    def click_usecases_card(self):
        """Open the org's UseCases section. Returns a UseCasesListPage."""
        from pages.provider.usecases_list_page import UseCasesListPage
        from locators.provider.usecases_list_page_locators import UseCaseListPageLocators

        self._open_sidebar_section(OrgLocators.USECASES_NAV_LINK, "/usecases", "UseCases")
        self.wait_with_timeout(15).until(
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for UseCases page to load"
        )
        return UseCasesListPage(self.driver)

    def click_collaboratives_card(self):
        """Open the org's Collaboratives section. Returns a CollaborativesListPage.

        test_prv_011's CI screenshot shows the click leaving the page on Datasets.
        The old fallback, any element containing 'Collaborative', also matched the
        sidebar link itself, so the wait could pass without navigating.
        """
        from pages.provider.collaboratives_list_page import CollaborativesListPage
        from locators.provider.collaboratives_list_page_locators import CollaborativesListPageLocators

        self._open_sidebar_section(OrgLocators.COLLABORATIVES_NAV_LINK, "collaboratives", "Collaboratives")
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON),
            message="Timed out waiting for 'Add New Collaborative' button"
        )
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
