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

    def is_loaded(self):
        return self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON)
        )

    def click_add_new_usecase(self):
        """
        Click the "Add New UseCase" button and wait for the create usecase form to load.

        Returns:
            CreateUsecasePage instance after the form has loaded
        """
        import time

        # Wait for the button to be clickable before clicking
        button = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for 'Add New UseCase' button to be clickable"
        )
        button.click()

        # Give the modal/form time to appear
        time.sleep(2)

        # Wait for the UseCase creation form to load by checking for the summary textarea
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(CreateUsecaseLocators.USECASE_SUMMARY_INPUT),
            message="Timed out waiting for UseCase creation form to load"
        )

        return CreateUsecasePage(self.driver)

