# locators/consumer/dataset_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class DatasetLocators:
    """XPaths for elements on the Datasets page."""

    # All dataset-card containers - match the actual class
    CARD = (By.XPATH, "//div[contains(@class, 'datasets_List')]")

    # First card only - the first link inside a dataset card
    FIRST_CARD = (By.XPATH, "(//div[contains(@class, 'datasets_List')]//a[@href[contains(., '/datasets/')]])[1]")

    # The "Download" link inside a dataset-card
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(@class, 'flex') and contains(@class, 'justify-center')] | //a[contains(., 'Download')]")
