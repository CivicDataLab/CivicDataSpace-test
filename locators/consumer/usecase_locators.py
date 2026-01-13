# locators/consumer/usecase_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class UseCaseLocators:
    """XPaths for elements on the Use Cases page."""

    # The page header ("Our Use Cases")
    HEADER = (By.XPATH, "//main//span[contains(., 'Use Case') or contains(., 'UseCases')] | //main//h1[contains(., 'Use Case')]")

    # All usecase-card containers
    CARD = (By.XPATH, "//div[contains(@class, 'usecase-card') or contains(@class, 'UseCaseCard')]")

    # First UseCase
    UC_FIRST_CARD = (By.XPATH, "(//div[contains(@class, 'usecase-card') or contains(@class, 'UseCaseCard')]//a)[1]")

    # First Dataset under Usecase
    UC_DATASET_FIRST_CARD = (By.XPATH, "(//div[contains(@class, 'dataset-card') or contains(@class, 'DatasetCard')]//a)[1]")

    # Download link for dataset under use case
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(@class, 'flex') and contains(@class, 'justify-center')] | //a[contains(., 'Download')]")
