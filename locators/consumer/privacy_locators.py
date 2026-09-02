# locators/consumer/privacy_locators.py
#
# Selectors for the privacy policy page (/privacy).

from selenium.webdriver.common.by import By


class PrivacyLocators:
    HEADING = (By.CSS_SELECTOR, "main h1, h1")
    MAIN_CONTENT = (By.CSS_SELECTOR, "main")
