# pages/consumer/dataset_page.py
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.consumer.dataset_locators import DatasetLocators

class DatasetPage(BasePage):
    """Encapsulates interactions on the Datasets tab / page."""

    def is_loaded(self) -> bool:
        """Wait for at least one dataset card to be visible."""
        self.wait.until(EC.visibility_of_element_located((By.XPATH, DatasetLocators.CARD)))
        return True

    def list_cards(self):
        """Wait for dataset cards to be present, then return them."""
        return self.finds((By.XPATH, DatasetLocators.CARD))

    def download_dataset(self, index: int = 0):
        """
        Wait for the first card to be clickable, then click its Download link.
        Returns (status_code, href).
        """
        # wait for card container
        card = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, DatasetLocators.FIRST_CARD))
        )
        card.click()

        # wait for dataset page load
        dataset_page = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, DatasetLocators.DOWNLOAD_LINK))
        )

        # find and click download
        link = dataset_page.find_element(By.XPATH, DatasetLocators.DOWNLOAD_LINK)
        href = link.get_attribute("href")
        if not href:
            raise AssertionError("Download link has no href")

        # verify URL
        status = requests.head(href, allow_redirects=True, timeout=10).status_code
        return href, status
