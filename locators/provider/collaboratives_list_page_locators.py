# locators/provider/collaboratives_list_page_locators.py
from selenium.webdriver.common.by import By

class CollaborativesListPageLocators:
    # Broad locator used only for page-load detection (not for clicking)
    ADD_NEW_COLLABORATIVE_BUTTON = (By.XPATH, "//*[contains(normalize-space(), 'Add New Collaborative')]")
