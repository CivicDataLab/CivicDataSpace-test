# locators/consumer/publishers_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class PublishersLocators:
    """XPaths for elements on the Publishers page."""

    # The page header ("Our Publishers")
    # Confirmed from a real captured DOM at failure time (test_con_008's new
    # diagnostics): the heading is an actual <h1>, not a span -- the opposite
    # mistake from the privacy page's locator, and the actual root cause of
    # every "timeout" here (two timeout bumps never had a chance to help).
    HEADER = (By.XPATH, "//h1[normalize-space(.)='Our Publishers']")

    # The three tab buttons
    TAB_ALL = (By.XPATH, "//button[normalize-space(.)='All Publishers']")
    TAB_ORG = (By.XPATH, "//button[normalize-space(.)='Organizations']")
    TAB_IND = (By.XPATH, "//button[normalize-space(.)='Individual Publishers']")

    # The grid wrapper that contains all cards (detects any link into /publishers/<id>)
    GRID_CONTAINER = (By.XPATH, "//div[contains(@class,'grid') and .//a[contains(@href,'/publishers/')]]")

    # Individual publisher cards: the <a> elements under that grid
    PUBLISHER_CARD = (By.XPATH, "//div[contains(@class,'grid')]//a[contains(@href,'/publishers/') and contains(@class,'shadow-card')]")

    # All Publishers button (alternative reference)
    ALL_PUBLISHERS_BUTTON = TAB_ALL

    # All publisher cards
    ALL_CARD = PUBLISHER_CARD

    # Usecase cards on publisher detail page - using actual structure
    USECASE_CARD = (By.XPATH, "//a[@href[contains(., '/usecases/')]][contains(@class, 'shadow-card')]")

    # First usecase card link
    ALL_UC_FIRST_CARD = (By.XPATH, "//a[@href[contains(., '/usecases/')]]")

    # All usecase cards container
    All_UC_Card = (By.XPATH, "//a[@href[contains(., '/usecases/')]]")
