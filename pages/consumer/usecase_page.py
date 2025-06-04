# pages/consumer/usecase_page.py
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


    def download_first_associated_dataset(self, usecase_index: int = 0, dataset_index: int = 0):
        """
        Click into the Nth sector, then the Mth dataset under it, grab the Download link,
        HEAD it, and assert both presence and HTTP‐200 in‐method.
        Returns (href, status_code).
        """
        # 1) click the Nth sector’s link
        sector_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH,
                                        f"({UseCaseLocators.UC_FIRST_CARD})[{usecase_index + 1}]"
                                        ))
        )
        sector_link.click()

        # 2) click the Mth dataset card
        dataset_card = self.wait.until(
            EC.element_to_be_clickable((By.XPATH,
                                        f"({UseCaseLocators.UC_DATASET_FIRST_CARD})[{dataset_index + 1}]"
                                        ))
        )
        dataset_card.click()

        # 3) find & wait for the Download link
        download_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, UseCaseLocators.DOWNLOAD_LINK))
        )
        href = download_link.get_attribute("href")

        # 4) assert the href is non‐empty
        assert href, "Download link has no href attribute"

        # 5) HEAD the URL
        status = requests.head(href, allow_redirects=True, timeout=10).status_code

        # 6) assert we got 2xx back
        assert 200 <= status < 300, f"Download HEAD returned HTTP {status}"

        return href, status

