# pages/provider/my_dashboard_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.provider.my_dashboard_locators import MyDashboardLocators
from pages.provider.create_dataset_page import CreateDatasetPage
from pages.provider.usecases_list_page import UseCasesListPage

class MyDashboardPage(BasePage):
    """
    POM for the Provider “My Dashboard” area (which you reach after logging in).
    There is a “My Dashboard” card → click it, then a sidebar appears; you click “Datasets”,
    and that reveals the “Drafts” tab (and the “Add New Dataset” button inside it).
    """

    def click_usecases_card(self):
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, MyDashboardLocators.USECASES_NAV_LINK)),
            message="Timed out waiting for the 'Usecases' card to be clickable"
        ).click()
        return UseCasesListPage(self.driver)

    def load(self):
        """
        (Optional) If you want to skip login and drive directly to /dashboard,
        you could visit(“/dashboard”). But in our tests we always login first.
        """
        self.visit(self.base_url + "/dashboard")

    def is_loaded(self, timeout: int = 10) -> bool:
        """
        Verify that at least the “My Dashboard” card is visible (this is the first screen you see
        after login). We do *not* yet assume we are inside the Datasets panel.
        Tests should call `is_loaded()` right after obtaining a MyDashboardPage
        to ensure that the login redirect finished.
        """
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(
                (By.XPATH, MyDashboardLocators.CARD_MY_DASHBOARD)
            ),
            message="Timed out waiting for the 'My Dashboard' card to appear on the Provider landing page"
        )
        return True

    def goto_my_dashboard(self) -> "MyDashboardPage":
        """
        Click the big “My Dashboard” c  ard on /dashboard. This reveals the sidebar menu.
        Returns self (so tests can chain further calls).
        """
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, MyDashboardLocators.CARD_MY_DASHBOARD)),
            message="Timed out waiting for the 'My Dashboard' card to be clickable"
        ).click()
        return self

    def click_datasets_sidebar(self) -> "MyDashboardPage":
        """
        Once the sidebar appears, click “Datasets” so that the Drafts/Published table loads.
        Returns self (so tests can chain).
        """
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, MyDashboardLocators.SIDEBAR_DATASETS)),
            message="Timed out waiting for the 'Datasets' link in sidebar to be clickable"
        ).click()
        return self

    def click_add_new_dataset(self) -> CreateDatasetPage:
        """
        1) Ensure “My Dashboard” card (role=button) is visible & clicked,
           as well as selecting “Datasets” in the sidebar.
        2) Wait until “Drafts” tab label is visible (meaning the Datasets panel fully loaded).
        3) Then wait for the “Add New Dataset” button to become clickable.
        4) Scroll it into view, click it, and hand back CreateDatasetPage.

        Usage in test:
            my_dash = prov_home.goto_my_dashboard().click_datasets_sidebar()
            create_ds = my_dash.click_add_new_dataset()
        """

        # Step A: Make sure we are “inside” My Dashboard. If tests already did `.goto_my_dashboard()`,
        # then the “My Dashboard” card is already clicked. In most test flows, we do:
        #     prov_home = home.go_to_login(flow="provider")
        #     my_dash = prov_home.goto_my_dashboard()               ← this clicks the card
        #     my_dash.click_datasets_sidebar()                     ← clicks “Datasets” in sidebar
        #
        # But if a caller forgot `.goto_my_dashboard()`, we still can try to click it here. So:
        try:
            # If “My Dashboard” card is still visible, click it once.
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, MyDashboardLocators.CARD_MY_DASHBOARD))
            ).click()
        except:
            # If it’s not there, maybe they already clicked it. Either way—proceed.
            pass

        # Step C: Wait for the “Drafts” tab to appear. This ensures the Datasets panel is fully rendered.
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, MyDashboardLocators.DRAFTS_TAB)),
            message="Timed out waiting for the 'Drafts' tab to appear"
        )

        # Step D: Now wait for “Add New Dataset” button to be clickable:
        btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, MyDashboardLocators.ADD_NEW_DATASET_BTN)),
            message="Timed out waiting for the 'Add New Dataset' button to become clickable"
        )

        # Step E: Scroll that button into view (just in case) and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        ActionChains(self.driver).move_to_element(btn).click().perform()

        # Step F: Return a CreateDatasetPage so tests can continue:
        return CreateDatasetPage(self.driver)
