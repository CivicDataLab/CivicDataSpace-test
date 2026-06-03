# locators/consumer/publisher_detail_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class PublisherDetailLocators:
    """XPaths for elements on a Publisher's detail page."""

    # Grid wrapper for use-case cards
    USECASE_GRID = (By.XPATH, "//div[contains(@class,'grid') and .//a[contains(@href,'/usecases/')]]")

    # The individual <a> cards under that grid
    USECASE_CARD = (By.XPATH, "//div[contains(@class,'grid')]//a[contains(@href,'/usecases/')]")
