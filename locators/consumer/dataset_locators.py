# locators/consumer/dataset_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class DatasetLocators:
    """XPaths for elements on the Datasets page."""

    # All dataset-card containers
    CARD = (By.XPATH, "//main//a[@href[contains(., '/datasets/')]]")

    # First card only
    FIRST_CARD = (By.XPATH, "(//main//a[@href[contains(., '/datasets/')]])[1]")

    # The "Download" link inside a dataset-card
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(., 'Download')] | //a[contains(@href, 'download')] | //button[contains(., 'Download')] | //a[contains(@class, 'flex') and contains(@class, 'justify-center')]")
