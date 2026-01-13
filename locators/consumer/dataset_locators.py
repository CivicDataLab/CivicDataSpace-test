# locators/consumer/dataset_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class DatasetLocators:
    """XPaths for elements on the Datasets page."""

    # All dataset-card containers
    CARD = (By.XPATH, "//div[contains(@class, 'dataset-card') or contains(@class, 'DatasetCard')]")

    # First card only
    FIRST_CARD = (By.XPATH, "//div[contains(@class, 'container')]//a[1]")

    # The "Download" link inside a dataset-card
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(@class, 'flex') and contains(@class, 'justify-center')] | //a[contains(., 'Download')]")
