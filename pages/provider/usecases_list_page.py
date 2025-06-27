# pages/provider/usecases_list_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from pages.provider.create_usecase_page import CreateUsecasePage
from locators.provider.usecases_list_page_locators import UseCaseListPageLocators


class UseCasesListPage(BasePage):

    def __init__(self, driver):
        self.driver = driver

    def is_loaded(self):
        return WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON)
        )

    def click_add_new_usecase(self):
        self.driver.find_element(*UseCaseListPageLocators.ADD_NEW_USECASE_BUTTON).click()
        return CreateUsecasePage(self.driver)

