# locators/consumer/search_locators.py
#
# Selectors for the unified search page (/search).

from selenium.webdriver.common.by import By


class SearchLocators:
    # DataSpaceFrontend#511's friendly error state, shown when the backend
    # search call fails. Matched by text since it is rendered as a styled
    # <Text> span, not a semantic error element.
    UNABLE_TO_LOAD_MESSAGE = (
        By.XPATH,
        "//*[contains(normalize-space(.), 'Unable to load results')]",
    )
