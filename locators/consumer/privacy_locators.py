# locators/consumer/privacy_locators.py
#
# Selectors for the privacy policy page (/privacy).

from selenium.webdriver.common.by import By


class PrivacyLocators:
    # The page renders its heading as a styled <span> (opub-ui's Text
    # component), not a real <h1> -- confirmed live: `main h1, h1` never
    # matches anything, so this timed out regardless of the URL being
    # correct. Match by text instead, same approach as PublishersLocators.HEADER.
    HEADING = (By.XPATH, "//span[normalize-space(.)='Privacy Policy']")
    MAIN_CONTENT = (By.CSS_SELECTOR, "main")
