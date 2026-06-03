# locators/provider/usecases_list_page_locators.py
from selenium.webdriver.common.by import By

class UseCaseListPageLocators:
    ADD_NEW_USECASE_BUTTON = (By.XPATH, "//button[normalize-space(.)='Add New UseCase']")