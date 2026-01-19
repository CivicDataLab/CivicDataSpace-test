# pages/provider/my_dashboard_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage
from locators.provider.my_dashboard_locators import MyDashboardLocators
from pages.provider.create_dataset_page import CreateDatasetPage
from pages.provider.usecases_list_page import UseCasesListPage
from pages.provider.update_profile_page import UpdateProfilePage

class MyDashboardPage(BasePage):
    """
    POM for the Provider “My Dashboard” area (which you reach after logging in).
    There is a “My Dashboard” card → click it, then a sidebar appears; you click “Datasets”,
    and that reveals the “Drafts” tab (and the “Add New Dataset” button inside it).
    """

    def load(self):
        """
        (Optional) If you want to skip login and drive directly to /dashboard,
        you could visit(“/dashboard”). But in our tests we always login first.
        """
        self.visit(self.base_url + "/dashboard")

    def is_loaded(self, timeout: int = 10) -> bool:
        """
        Verify that at least the "My Dashboard" card is visible (this is the first screen you see
        after login). We do *not* yet assume we are inside the Datasets panel.
        Tests should call `is_loaded()` right after obtaining a MyDashboardPage
        to ensure that the login redirect finished.
        """
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(MyDashboardLocators.CARD_MY_DASHBOARD),
            message="Timed out waiting for the 'My Dashboard' card to appear on the Provider landing page"
        )
        return True

    def goto_my_dashboard(self) -> "MyDashboardPage":
        """
        Click the big "My Dashboard" c  ard on /dashboard. This reveals the sidebar menu.
        Returns self (so tests can chain further calls).
        """
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.CARD_MY_DASHBOARD),
            message="Timed out waiting for the 'My Dashboard' card to be clickable"
        ).click()
        return self

    def click_datasets_sidebar(self) -> "MyDashboardPage":
        """
        Once the sidebar appears, click "Datasets" so that the Drafts/Published table loads.
        Returns self (so tests can chain).
        """
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.SIDEBAR_DATASETS),
            message="Timed out waiting for the 'Datasets' link in sidebar to be clickable"
        ).click()
        return self

    def click_add_new_dataset(self) -> CreateDatasetPage:
        """
        1) Ensure "My Dashboard" card (role=button) is visible & clicked,
           as well as selecting "Datasets" in the sidebar.
        2) Wait until "Drafts" tab label is visible (meaning the Datasets panel fully loaded).
        3) Then wait for the "Add New Dataset" button to become clickable.
        4) Click it to open the dataset type selection modal.
        5) Select "Data Dataset" option in the modal.
        6) Click "Create Dataset" button to proceed.
        7) Return CreateDatasetPage once the metadata form loads.

        Usage in test:
            my_dash = prov_home.goto_my_dashboard().click_datasets_sidebar()
            create_ds = my_dash.click_add_new_dataset()
        """
        from locators.provider.create_dataset_locators import CreateDatasetLocators

        try:
            # If "My Dashboard" card is still visible, click it once.
            self.wait_with_timeout(3).until(
                EC.element_to_be_clickable(MyDashboardLocators.CARD_MY_DASHBOARD)
            ).click()
        except TimeoutException:
            # If it's not there, maybe they already clicked it. Either way—proceed.
            pass

        # Step C: Wait for the "Drafts" tab to appear. This ensures the Datasets panel is fully rendered.
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(MyDashboardLocators.DRAFTS_TAB),
            message="Timed out waiting for the 'Drafts' tab to appear"
        )

        # Step D: Now wait for "Add New Dataset" button to be clickable:
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.ADD_NEW_DATASET_BTN),
            message="Timed out waiting for the 'Add New Dataset' button to become clickable"
        )

        # Step E: Scroll that button into view (just in case) and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        ActionChains(self.driver).move_to_element(btn).click().perform()

        # Step F: Wait for the "Create New Dataset" modal to appear
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.MODAL_TITLE)),
            message="Timed out waiting for 'Create New Dataset' modal to appear"
        )

        # Step G: Click the "Data Dataset" card option
        data_dataset_card = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DATA_DATASET_CARD)),
            message="Timed out waiting for 'Data Dataset' option to be clickable"
        )
        data_dataset_card.click()

        # Step H: Click the "Create Dataset" button to proceed
        create_btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.CREATE_DATASET_BUTTON)),
            message="Timed out waiting for 'Create Dataset' button to be clickable"
        )
        create_btn.click()

        # Step I: Wait for the metadata tab to appear (confirms we're in the dataset creation form)
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.TAB_METADATA)),
            message="Timed out waiting for Metadata tab to appear after creating dataset"
        )

        # Step J: Return a CreateDatasetPage so tests can continue:
        return CreateDatasetPage(self.driver)

    def click_usecases_card(self):
        from locators.provider.usecases_list_page_locators import UseCaseListPageLocators

        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.USECASES_NAV_LINK),
            message="Timed out waiting for the 'Usecases' card to be clickable"
        ).click()

        # Wait for the UseCases page to load by checking for the "Add New UseCase" button
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for UseCases page to load"
        )

        return UseCasesListPage(self.driver)

    def click_profile_card(self):
        from locators.provider.update_profile_locators import UpdateProfilePageLocators
        import time

        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.PROFILE_NAV_LINK),
            message="Timed out waiting for the 'Profile' card to be clickable"
        ).click()

        # Give the profile page time to load
        time.sleep(2)

        # Wait for the profile page to load by checking for the "My Profile" heading
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(UpdateProfilePageLocators.My_Profile_HEADING),
            message="Timed out waiting for Profile page to load"
        )

        return UpdateProfilePage(self.driver)