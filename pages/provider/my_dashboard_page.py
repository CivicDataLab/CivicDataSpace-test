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
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(MyDashboardLocators.ADD_NEW_DATASET_BTN),
            message="Timed out waiting for the 'Add New Dataset' button to appear on My Dashboard"
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
        from locators.provider.create_dataset_locators import CreateDatasetLocators

        # Wait for navigation to the dataset page to complete
        self.wait_with_timeout(15).until(
            lambda d: '/dataset' in d.current_url
        )

        # Locate the button and JS-click it (avoids element_to_be_clickable overlay issues)
        btn = self.wait_with_timeout(15).until(
            EC.presence_of_element_located(MyDashboardLocators.ADD_NEW_DATASET_BTN)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for the "Create New Dataset" type-selection modal
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

        # Wait for the metadata tab to confirm we're inside the creation form
        self.wait_with_timeout(30).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.TAB_METADATA)),
            message="Timed out waiting for Metadata tab to appear after creating dataset"
        )

        return CreateDatasetPage(self.driver)

    def click_add_new_prompt_dataset(self) -> CreateDatasetPage:
        from locators.provider.create_dataset_locators import CreateDatasetLocators

        self.wait_with_timeout(15).until(
            lambda d: '/dataset' in d.current_url
        )

        btn = self.wait_with_timeout(15).until(
            EC.presence_of_element_located(MyDashboardLocators.ADD_NEW_DATASET_BTN)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)

        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.MODAL_TITLE)),
            message="Timed out waiting for 'Create New Dataset' modal to appear"
        )

        prompt_card = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.PROMPT_DATASET_CARD)),
            message="Timed out waiting for 'Prompt Dataset' option to be clickable"
        )
        prompt_card.click()

        create_btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.CREATE_DATASET_BUTTON)),
            message="Timed out waiting for 'Create Dataset' button to be clickable"
        )
        create_btn.click()

        self.wait_with_timeout(30).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.TAB_METADATA)),
            message="Timed out waiting for Metadata tab after creating prompt dataset"
        )

        return CreateDatasetPage(self.driver)

    def click_usecases_card(self):
        from locators.provider.usecases_list_page_locators import UseCaseListPageLocators

        usecases_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.USECASES_NAV_LINK),
            message="Timed out waiting for the 'Usecases' card to be clickable"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", usecases_link)
        self.driver.execute_script("arguments[0].click();", usecases_link)

        # JS click occasionally doesn't trigger React's router (e.g. under server load right
        # after the previous test finishes). Retry once with a real click if URL hasn't changed.
        try:
            self.wait_with_timeout(8).until(lambda d: '/usecases' in d.current_url)
        except TimeoutException:
            usecases_link.click()
            self.wait_with_timeout(15).until(
                lambda d: '/usecases' in d.current_url,
                message="Timed out waiting for UseCases page URL after retry click"
            )

        self.wait_with_timeout(15).until(
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for UseCases page to load"
        )

        return UseCasesListPage(self.driver)

    def click_collaboratives_card(self):
        from locators.provider.collaboratives_list_page_locators import CollaborativesListPageLocators
        from pages.provider.collaboratives_list_page import CollaborativesListPage

        collaboratives_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.COLLABORATIVES_NAV_LINK),
            message="Timed out waiting for the 'Collaboratives' card to be clickable"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", collaboratives_link)
        self.driver.execute_script("arguments[0].click();", collaboratives_link)

        # Same retry pattern as click_usecases_card: JS click occasionally doesn't trigger
        # React's router on CI runners. The broad text-based fallbacks that were here before
        # matched sidebar nav items already on screen, causing a false-positive early return.
        try:
            self.wait_with_timeout(8).until(lambda d: 'collaboratives' in d.current_url)
        except TimeoutException:
            collaboratives_link.click()
            self.wait_with_timeout(15).until(
                lambda d: 'collaboratives' in d.current_url,
                message="Timed out waiting for Collaboratives page URL after retry click"
            )

        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON),
            message="Timed out waiting for 'Add New Collaborative' button"
        )

        return CollaborativesListPage(self.driver)

    def click_ai_models_card(self):
        from pages.provider.ai_models_list_page import AiModelsListPage
        from selenium.common.exceptions import TimeoutException

        ai_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.AI_MODELS_NAV_LINK),
            message="Timed out waiting for 'AI Models' nav link"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ai_link)
        self.driver.execute_script("arguments[0].click();", ai_link)

        try:
            self.wait_with_timeout(8).until(lambda d: '/aimodels' in d.current_url)
        except TimeoutException:
            ai_link.click()
            self.wait_with_timeout(15).until(
                lambda d: '/aimodels' in d.current_url,
                message="Timed out waiting for AI Models page URL after retry"
            )

        return AiModelsListPage(self.driver)

    def click_charts_card(self):
        from locators.provider.charts_locators import ChartsLocators
        from pages.provider.charts_list_page import ChartsListPage

        charts_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.CHARTS_NAV_LINK),
            message="Timed out waiting for 'Add & Manage Charts' link to be clickable"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", charts_link)
        self.driver.execute_script("arguments[0].click();", charts_link)

        try:
            self.wait_with_timeout(8).until(lambda d: '/charts' in d.current_url)
        except TimeoutException:
            charts_link.click()
            self.wait_with_timeout(15).until(
                lambda d: '/charts' in d.current_url,
                message="Timed out waiting for Charts page URL after retry click"
            )

        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(ChartsLocators.ADD_CHART_BTN),
            message="Timed out waiting for 'Add Chart' button on Charts page"
        )
        return ChartsListPage(self.driver)

    def click_profile_card(self):
        from locators.provider.update_profile_locators import UpdateProfilePageLocators
        import time

        # Wait for and click the Profile navigation link
        profile_link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(MyDashboardLocators.PROFILE_NAV_LINK),
            message="Timed out waiting for the 'Profile' card to be clickable"
        )

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", profile_link)
        profile_link.click()

        # Give the page time to navigate
        time.sleep(2)

        # Wait for the profile page to load by checking for the "My Profile" heading
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(UpdateProfilePageLocators.My_Profile_HEADING),
            message="Timed out waiting for Profile page to load"
        )

        return UpdateProfilePage(self.driver)