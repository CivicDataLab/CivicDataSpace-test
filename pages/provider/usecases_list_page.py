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
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON)
        )

    def click_add_new_usecase(self):
        import time

        # Locate the button and JS-click (avoids hidden-tab duplicate issues)
        btn = self.wait_with_timeout(10).until(
            EC.presence_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON),
            message="Timed out waiting for 'Add New UseCase' button"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)

        time.sleep(1)

        # Wait for the UseCase creation form
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(CreateUsecaseLocators.USECASE_SUMMARY_INPUT),
            message="Timed out waiting for UseCase creation form to load"
        )

        return CreateUsecasePage(self.driver)

