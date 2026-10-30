# locators/provider/collaboratives_list_page_locators.py
from selenium.webdriver.common.by import By

class CollaborativesListPageLocators:
    # Broad locator used only for page-load detection (not for clicking)
    ADD_NEW_COLLABORATIVE_BUTTON = (By.XPATH, "//*[contains(normalize-space(), 'Create Collaborative')]")

    # One empty-state cell for every tab; LIST_ROWS skips it.
    EMPTY_DRAFTS_MESSAGE = (By.XPATH, "//table//tbody//td[contains(@class,'EmptyCell')]")
    EMPTY_PUBLISHED_MESSAGE = EMPTY_DRAFTS_MESSAGE
    LIST_ROWS = (By.XPATH, "//table//tbody/tr[not(td[contains(@class,'EmptyCell')])]")
