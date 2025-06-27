# locators/provider/usecases_list_page_locators.py
from selenium.webdriver.common.by import By

class UseCaseListPageLocators:
    ADD_NEW_USECASE_BUTTON = (By.XPATH, "//div[@class='flex items-center gap-3']//span[@class='Button-module_removeUnderline__dq0ct'][normalize-space()='Add New UseCase']")