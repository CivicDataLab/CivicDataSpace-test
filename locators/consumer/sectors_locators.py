# locators/consumer/sectors_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class SectorsLocators:
    """XPaths for elements on the Sectors page."""

    # The page header ("Our Sectors")
    HEADER = (By.XPATH, "//main//span[contains(., 'Sectors') or contains(., 'Our Sectors')] | //main//h1[contains(., 'Sectors')]")

    # All sector-card containers
    SEC_CARD = (By.XPATH, "//div[contains(@class, 'sector-card') or contains(@class, 'SectorCard')]")

    # First Sector Card
    SEC_FIRST_CARD = (By.XPATH, "(//div[contains(@class, 'sector-card') or contains(@class, 'SectorCard')]//a)[1]")

    # All dataset cards under a sector page
    SEC_DATASET_CARD = (By.XPATH, "//div[contains(@class, 'dataset-card') or contains(@class, 'DatasetCard')]")

    # First dataset card under a sector page
    SEC_DATASET_FIRST_CARD = (By.XPATH, "(//div[contains(@class, 'dataset-card') or contains(@class, 'DatasetCard')]//a)[1]")

    # Download link of the first dataset
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(@class, 'flex') and contains(@class, 'justify-center')] | //a[contains(., 'Download')]")
