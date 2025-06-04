# locators/consumer/publisher_detail_locators.py

class PublisherDetailLocators:
    """XPaths for elements on a Publisher's detail page."""

    # grid wrapper for use-case cards
    USECASE_GRID = "//div[contains(@class,'grid') and .//a[contains(@href,'/usecases/')]]"

    # the individual <a> cards under that grid
    USECASE_CARD = USECASE_GRID + "//a[contains(@href,'/usecases/')]"
