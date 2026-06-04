# locators/consumer/usecase_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class UseCaseLocators:
    """XPaths for elements on the Use Cases page."""

    # The page header ("Our Use Cases")
    HEADER = (By.XPATH, "//main//span[contains(., 'Use Case') or contains(., 'UseCases')] | //main//h1[contains(., 'Use Case')]")

    # All usecase-card containers
    CARD = (By.XPATH, "//main//a[@href[contains(., '/usecases/')]]")

    # First UseCase - clickable link
    UC_FIRST_CARD = (By.XPATH, "//a[@href[contains(., '/usecases/')]]")

    # First Dataset under Usecase - using actual class
    UC_DATASET_FIRST_CARD = (By.XPATH, "//div[contains(@class, 'datasets_List')]//a[@href[contains(., '/datasets/')]]")

    # Download link for dataset under use case
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(@class, 'flex') and contains(@class, 'justify-center')] | //a[contains(., 'Download')]")
