# locators/provider/usecases_list_page_locators.py
from selenium.webdriver.common.by import By

class UseCaseListPageLocators:
    ADD_NEW_USECASE_BUTTON = (By.XPATH, "//button[normalize-space(.)='Add New UseCase']")
    # Empty-list states. Which one renders depends on the drafts/published tab.
    EMPTY_DRAFTS_MESSAGE = (By.XPATH, "//*[normalize-space(text())='You have not added any usecase yet.']")
    EMPTY_PUBLISHED_MESSAGE = (By.XPATH, "//*[normalize-space(text())='No Published UseCases yet.']")
    LIST_ROWS = (By.XPATH, "//table//tbody/tr")
