# locators/provider/usecases_list_page_locators.py
from selenium.webdriver.common.by import By

class UseCaseListPageLocators:
    ADD_NEW_USECASE_BUTTON = (By.XPATH, "//button[normalize-space(.)='Create Use Case']")
    # One empty-state cell for every tab; LIST_ROWS skips it.
    EMPTY_DRAFTS_MESSAGE = (By.XPATH, "//table//tbody//td[contains(@class,'EmptyCell')]")
    EMPTY_PUBLISHED_MESSAGE = EMPTY_DRAFTS_MESSAGE
    LIST_ROWS = (By.XPATH, "//table//tbody/tr[not(td[contains(@class,'EmptyCell')])]")
