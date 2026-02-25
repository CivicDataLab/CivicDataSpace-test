# locators/consumer/about_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class AboutLocators:
    """XPaths for elements on the About Us page."""

    # The main heading in the About section
    HEADING = (By.XPATH, "//main//*[self::h1 or self::h2 or self::span][contains(., 'About CivicDataSpace')]")

    # A representative paragraph under the heading
    PARAGRAPH = (By.XPATH, "//main//div[contains(@class, 'container')]//span[contains(., 'CivicDataSpace is')]")
