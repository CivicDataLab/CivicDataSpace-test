# locators/consumer/sectors_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class SectorsLocators:
    """XPaths for elements on the Sectors page."""

    # The page header ("Our Sectors")
    HEADER = (By.XPATH, "//main//span[contains(., 'Sectors') or contains(., 'Our Sectors')] | //main//h1[contains(., 'Sectors')]")

    # All sector-card containers
    SEC_CARD = (By.XPATH, "//main//a[@href[contains(., '/sectors/')]]")

    # First Sector Card - clickable link
    SEC_FIRST_CARD = (By.XPATH, "//a[@href[contains(., '/sectors/')]]")

    # All dataset cards under a sector page - using the actual class
    SEC_DATASET_CARD = (By.XPATH, "//div[contains(@class, 'datasets_List')]")

    # First dataset card under a sector page - clickable link
    SEC_DATASET_FIRST_CARD = (By.XPATH, "//main//a[@href[contains(., '/datasets/')]]")

    # Download link of the first dataset
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(., 'Download')] | //a[contains(@href, 'download')] | //button[contains(., 'Download')] | //a[contains(@class, 'flex') and contains(@class, 'justify-center')]")
