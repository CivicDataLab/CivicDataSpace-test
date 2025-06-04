# pages/consumer/publishers_page.py

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
from pages.base_page import BasePage
from locators.consumer.publishers_locators import PublishersLocators
from pages.consumer.publisher_detail_page import PublisherDetailPage

logger = logging.getLogger(__name__)

class PublishersPage(BasePage):
    def is_loaded(self) -> bool:
        """Wait for ‘Our Publishers’ header to be visible."""
        return self.find((By.XPATH, PublishersLocators.HEADER)).is_displayed()

    def _select_tab(self, xpath: str):
        """Helper: click a tab button by its XPath."""
        logger.info("Selecting tab via %s", xpath)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

    def list_all_publishers(self):
        """
        Ensure the ‘All Publishers’ view is active (click the tab if needed),
        then return a list of all publisher‐card WebElements.
        """
        # if there is an explicit “All Publishers” button/tab, click it:
        try:
            self.click((By.XPATH, PublishersLocators.ALL_PUBLISHERS_BUTTON))
        except:
            # assume All is default
            pass

        # wait for cards to appear
        return self.finds((By.XPATH, PublishersLocators.ALL_CARD))

    def list_publishers(self, view: str = "all"):
        """
        Click the correct tab ('all','org','ind'), then return all <a> cards.
        """
        tab_map = {
            "all": PublishersLocators.TAB_ALL,
            "org": PublishersLocators.TAB_ORG,
            "ind": PublishersLocators.TAB_IND,
        }
        tab_xpath = tab_map.get(view)
        if not tab_xpath:
            raise ValueError(f"Unknown view '{view}'")

        # click the tab
        self._select_tab(tab_xpath)

        # wait for the grid container to show up
        self.wait.until(EC.presence_of_element_located((By.XPATH, PublishersLocators.GRID_CONTAINER)))

        # return all the <a> publisher cards
        return self.finds((By.XPATH, PublishersLocators.PUBLISHER_CARD))


    def open_publisher_by_index(self, index: int = 0, view: str = "all") -> "PublisherDetailPage":
        """
        From the given view, click the Nth publisher card.
        Returns a PublisherDetailPage, which you can use to drill into its use cases.
        """
        cards = self.list_publishers(view)
        if len(cards) <= index:
            raise AssertionError(f"No publisher at index {index} in view '{view}' (found {len(cards)})")
        # click the link
        cards[index].click()

        # hand off to the detail page object
        return PublisherDetailPage(self.driver, publisher_type=view)

    def list_usecase_cards(self):
        """Return all usecase‐card elements on the publisher detail page."""
        return self.finds((By.XPATH, PublishersLocators.USECASE_CARD))

    def open_usecase_by_index(self, index: int = 0):
        """
        Click the usecase-card link at position `index`,
        re-locating fresh so it can't go stale.
        """
        link_locator = (
            By.XPATH,
            f"({PublishersLocators.All_UC_Card})[{index+1}]"
            f"{PublishersLocators.ALL_UC_FIRST_CARD}"
        )
        self.wait.until(EC.element_to_be_clickable(link_locator)).click()
        return self