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
        # The create mutation plus the navigation it triggers is the slow step;
        # 30s was not enough under concurrent load.
        self.wait_with_timeout(60).until(
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

        # The create mutation plus the navigation it triggers is the slow step;
        # 30s was not enough under concurrent load.
        self.wait_with_timeout(60).until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.TAB_METADATA)),
            message="Timed out waiting for Metadata tab after creating prompt dataset"
        )

        return CreateDatasetPage(self.driver)

    def _open_sidebar_section(self, link_locator, url_part: str, name: str) -> None:
        """Click a dashboard sidebar link and wait until the URL actually changes.

        A click sometimes lands before the Next.js router is ready and nothing
        navigates: the link highlights but the page stays put (seen on the CI
        runner for UseCases, Collaboratives, AI Models, Charts and Profile). So
        confirm the URL moved, and click once more, re-found, if it didn't.
        """
        link = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(link_locator),
            message=f"Timed out waiting for the '{name}' link to be clickable",
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        self.driver.execute_script("arguments[0].click();", link)
        try:
            self.wait_with_timeout(8).until(lambda d: url_part in d.current_url)
        except TimeoutException:
            self.wait_with_timeout(10).until(EC.element_to_be_clickable(link_locator)).click()
            self.wait_with_timeout(15).until(
                lambda d: url_part in d.current_url,
                message=f"Timed out waiting for the {name} page URL after retry click",
            )

    def click_usecases_card(self):
        from locators.provider.usecases_list_page_locators import UseCaseListPageLocators

        self._open_sidebar_section(MyDashboardLocators.USECASES_NAV_LINK, "/usecases", "UseCases")

        self.wait_with_timeout(15).until(
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for UseCases page to load"
        )

        return UseCasesListPage(self.driver)

    def click_collaboratives_card(self):
        from locators.provider.collaboratives_list_page_locators import CollaborativesListPageLocators
        from pages.provider.collaboratives_list_page import CollaborativesListPage

        self._open_sidebar_section(
            MyDashboardLocators.COLLABORATIVES_NAV_LINK, "collaboratives", "Collaboratives"
        )

        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON),
            message="Timed out waiting for 'Add New Collaborative' button"
        )

        return CollaborativesListPage(self.driver)

    def click_ai_models_card(self):
        from pages.provider.ai_models_list_page import AiModelsListPage

        self._open_sidebar_section(MyDashboardLocators.AI_MODELS_NAV_LINK, "/aimodels", "AI Models")

        return AiModelsListPage(self.driver)

    def click_charts_card(self):
        from locators.provider.charts_locators import ChartsLocators
        from pages.provider.charts_list_page import ChartsListPage

        self._open_sidebar_section(MyDashboardLocators.CHARTS_NAV_LINK, "/charts", "Charts")

        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(ChartsLocators.ADD_CHART_BTN),
            message="Timed out waiting for 'Add Chart' button on Charts page"
        )
        return ChartsListPage(self.driver)

    def click_profile_card(self):
        from locators.provider.update_profile_locators import UpdateProfilePageLocators

        self._open_sidebar_section(MyDashboardLocators.PROFILE_NAV_LINK, "/profile", "Profile")

        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(UpdateProfilePageLocators.My_Profile_HEADING),
            message="Timed out waiting for Profile page to load"
        )

        return UpdateProfilePage(self.driver)