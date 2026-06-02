# locators/consumer/about_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class AboutLocators:
    """XPaths for elements on the About Us page."""

    # The main heading in the About section
    HEADING = (By.XPATH, "//main//*[normalize-space(.)='About CivicDataSpace' or contains(normalize-space(.), 'About CivicDataSpace')]")

    # A representative paragraph under the heading
    PARAGRAPH = (By.XPATH, "//main//*[contains(normalize-space(.), 'CivicDataSpace is')]")
