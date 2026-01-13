# locators/consumer/about_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class AboutLocators:
    """XPaths for elements on the About Us page."""

    # The main heading in the About section
    HEADING = (By.XPATH, "//main//span[contains(., 'About') or preceding::h1[contains(., 'About')]] | //main//h1[contains(., 'About')]")

    # A representative paragraph under the heading
    PARAGRAPH = (By.XPATH, "//main//span[2] | //main//p[contains(@class, 'description') or contains(@class, 'about')]")
