# locators/consumer/publishers_locators.py

class PublishersLocators:
    """XPaths for elements on the Use Cases page."""

    # The page header (“Our Publishers”)
    HEADER = "//span[normalize-space(.)='Our Publishers']"

    # the three tab buttons
    TAB_ALL = "//button[normalize-space(.)='All Publishers']"
    TAB_ORG = "//button[normalize-space(.)='Organizations']"
    TAB_IND = "//button[normalize-space(.)='Individual Publishers']"

    # the grid wrapper that contains all cards (detects any link into /publishers/<id>)
    GRID_CONTAINER = "//div[contains(@class,'grid') and .//a[contains(@href,'/publishers/')]]"

    # individual publisher cards: the <a> elements under that grid
    PUBLISHER_CARD = GRID_CONTAINER + "//a[contains(@href,'/publishers/') and contains(@class,'shadow-card')]"
