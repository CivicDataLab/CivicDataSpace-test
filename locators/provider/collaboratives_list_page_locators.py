# locators/provider/collaboratives_list_page_locators.py
from selenium.webdriver.common.by import By

class CollaborativesListPageLocators:
    # Broad locator used only for page-load detection (not for clicking)
    ADD_NEW_COLLABORATIVE_BUTTON = (By.XPATH, "//*[contains(normalize-space(), 'Add New Collaborative')]")

    # Empty-list states. Which one renders depends on the drafts/published tab.
    EMPTY_DRAFTS_MESSAGE = (By.XPATH, "//*[normalize-space(text())='You have not added any collaborative yet.']")
    EMPTY_PUBLISHED_MESSAGE = (By.XPATH, "//*[normalize-space(text())='No Published Collaboratives yet.']")
    LIST_ROWS = (By.XPATH, "//table//tbody/tr")
