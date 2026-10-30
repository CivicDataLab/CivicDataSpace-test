# pages/provider/usecases_list_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from pages.provider.create_usecase_page import CreateUsecasePage
from locators.provider.usecases_list_page_locators import UseCaseListPageLocators
from locators.provider.create_usecase_locators import CreateUsecaseLocators


class UseCasesListPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver)  # Initialize BasePage with self.wait

    def view_state(self) -> str:
        """'drafts_empty', 'published_empty' or 'rows' (see BasePage.list_view_state)."""
        return self.list_view_state(UseCaseListPageLocators)

    def is_loaded(self):
        return self.wait_with_timeout(10).until(
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON)
        )

    def click_add_new_usecase(self):
        """Click "Create Use Case"; it creates a draft and opens the Builder step."""
        self.click_until(
            UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON,
            EC.visibility_of_element_located(CreateUsecaseLocators.TITLE_INPUT),
            message="'Create Use Case' never opened the editor",
        )
        return CreateUsecasePage(self.driver)

