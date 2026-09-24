# pages/consumer/usecase_page.py
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from locators.consumer.usecase_locators import UseCaseLocators

class UseCasePage(BasePage):
    """Interactions on the Use Cases tab / page."""

    def is_loaded(self) -> bool:
        """Wait for 'Our Use Cases' header to be visible."""
        return self.find(UseCaseLocators.HEADER).is_displayed()

    def has_cards(self):
        """Wait for usecase cards to be present, then return them."""
        return self.finds(UseCaseLocators.CARD)

    # pages/consumer/usecase_page.py

    def download_first_associated_dataset(self, usecase_index: int = 0, dataset_index: int = 0):
        cards = self.driver.find_elements(*UseCaseLocators.UC_FIRST_CARD)
        if len(cards) <= usecase_index:
            return None  # Not enough use cases
        # ... the rest is unchanged
        sector_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"({UseCaseLocators.UC_FIRST_CARD[1]})[{usecase_index + 1}]")
            )
        )
        sector_link.click()
        datasets = self.driver.find_elements(*UseCaseLocators.UC_DATASET_FIRST_CARD)
        if len(datasets) <= dataset_index:
            return None  # Not enough datasets
        dataset_card = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"({UseCaseLocators.UC_DATASET_FIRST_CARD[1]})[{dataset_index + 1}]")
            )
        )
        dataset_card.click()
        download_link = self.wait.until(
            EC.element_to_be_clickable(UseCaseLocators.DOWNLOAD_LINK)
        )
        href = download_link.get_attribute("href")
        status = requests.head(href, allow_redirects=True, timeout=10).status_code
        return (href, status)

    # ── Use case detail page ─────────────────────────────────────────────────

    def open_detail(self, base_url: str, usecase_id):
        """Open /usecases/<id> and wait for the always-rendered datasets heading."""
        self.visit(f"{base_url.rstrip('/')}/usecases/{usecase_id}")
        self.find(UseCaseLocators.DETAIL_DATASETS_HEADING)
        return self

    def has_dashboards_section(self, timeout: int = 10) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(UseCaseLocators.DETAIL_DASHBOARDS_HEADING)
            )
            return True
        except TimeoutException:
            return False

    def embedded_dashboards(self):
        """[{title, src}] for each dashboard iframe on the detail page."""
        frames = self.finds(UseCaseLocators.DETAIL_DASHBOARD_IFRAME)
        return [{"title": f.get_attribute("title"), "src": f.get_attribute("src")} for f in frames]

    def dashboard_open_links(self):
        """[{href, target, rel}] for each 'Open dashboard in a new tab' link."""
        links = self.finds(UseCaseLocators.DETAIL_DASHBOARD_OPEN_LINK)
        return [
            {"href": a.get_attribute("href"), "target": a.get_attribute("target"), "rel": a.get_attribute("rel")}
            for a in links
        ]

    def dashboards_render_before_datasets(self) -> bool:
        dash = self.find(UseCaseLocators.DETAIL_DASHBOARDS_HEADING)
        datasets = self.find(UseCaseLocators.DETAIL_DATASETS_HEADING)
        return self.driver.execute_script(
            "return !!(arguments[0].compareDocumentPosition(arguments[1]) & Node.DOCUMENT_POSITION_FOLLOWING);",
            dash, datasets,
        )
