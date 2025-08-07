# pages/consumer/usecase_page.py
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
from pages.base_page import BasePage
from locators.consumer.usecase_locators import UseCaseLocators

class UseCasePage(BasePage):
    """Interactions on the Use Cases tab / page."""

    def is_loaded(self) -> bool:
        """Wait for ‘Our Use Cases’ header to be visible."""
        return self.find((By.XPATH, UseCaseLocators.HEADER)).is_displayed()
    
    def has_cards(self):
        """Wait for usecase cards to be present, then return them."""
        return self.finds((By.XPATH, UseCaseLocators.CARD))

    # pages/consumer/usecase_page.py

    def download_first_associated_dataset(self, usecase_index: int = 0, dataset_index: int = 0):
        cards = self.driver.find_elements(By.XPATH, UseCaseLocators.UC_FIRST_CARD)
        if len(cards) <= usecase_index:
            return None  # Not enough use cases
        # ... the rest is unchanged
        sector_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"({UseCaseLocators.UC_FIRST_CARD})[{usecase_index + 1}]")
            )
        )
        sector_link.click()
        datasets = self.driver.find_elements(By.XPATH, UseCaseLocators.UC_DATASET_FIRST_CARD)
        if len(datasets) <= dataset_index:
            return None  # Not enough datasets
        dataset_card = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"({UseCaseLocators.UC_DATASET_FIRST_CARD})[{dataset_index + 1}]")
            )
        )
        dataset_card.click()
        download_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, UseCaseLocators.DOWNLOAD_LINK))
        )
        href = download_link.get_attribute("href")
        status = requests.head(href, allow_redirects=True, timeout=10).status_code
        return (href, status)



