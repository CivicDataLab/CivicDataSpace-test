# locators/provider/provider_homepage_locators.py

from selenium.webdriver.common.by import By

class ProviderHomepageLocators:
    """XPaths for elements on the Provider Dashboard page."""

    # The main heading
    HEADER = (By.XPATH, "//span[contains(@class,'Text-module_headingXl') and normalize-space(.)='User Dashboard']")

    # The two cards you see: "My Dashboard" and "Organizations"
    CARD_MY_DASH     = (By.XPATH, "//a[contains(@href,'/dashboard') and .//span[normalize-space()='My Dashboard']]")
    CARD_ORGANIZATIONS = (By.XPATH, "//a[contains(@href,'/organization') and .//span[normalize-space()='Organizations']]")

