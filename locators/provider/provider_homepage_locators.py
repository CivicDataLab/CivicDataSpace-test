# locators/provider/provider_homepage_locators.py

class ProviderHomepageLocators:
    """XPaths for elements on the Provider Dashboard page."""

    # The main heading
    HEADER = "//span[contains(@class,'Text-module_headingXl') and normalize-space(.)='User Dashboard']"

    # The two cards you see: “My Dashboard” and “Organizations”
    CARD_MY_DASH     = "//a[contains(@href,'/dashboard') and .//span[normalize-space()='My Dashboard']]"
    CARD_ORGANIZATIONS = "//a[contains(@href,'/organization') and .//span[normalize-space()='Organizations']]"

