# pages/consumer/publishers_page.py

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import requests
from pages.base_page import BasePage
from locators.consumer.publishers_locators import PublishersLocators
from pages.consumer.publisher_detail_page import PublisherDetailPage

logger = logging.getLogger(__name__)

class PublishersPage(BasePage):
    def is_loaded(self) -> bool:
        """Wait for 'Our Publishers' header to be visible."""
        return self.find(PublishersLocators.HEADER).is_displayed()

    def _select_tab(self, locator: tuple, timeout: int = 10) -> None:
        """
        Clicks the tab (if not already active) with overlap-safe logic.
        Accepts a locator tuple like (By.XPATH, "xpath_string").
        """
        tab = self.wait_with_timeout(timeout).until(
            EC.presence_of_element_located(locator)
        )

        # Already selected?
        if "active" in tab.get_attribute("class"):
            return

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tab)

        # ----- safe-click with up to 3 attempts -----
        for attempt in range(3):
            try:
                self.wait_with_timeout(timeout).until(
                    EC.element_to_be_clickable(locator)
                )
                tab.click()
                return
            except ElementClickInterceptedException:
                # Wait a short moment for overlay/animation to clear, then retry
                self.wait_with_timeout(2).until(
                    lambda drv: drv.execute_script(
                        "return arguments[0].getBoundingClientRect().top >= 0 && "
                        "arguments[0].getBoundingClientRect().bottom <= (window.innerHeight || document.documentElement.clientHeight);",
                        tab,
                    )
                )
        # If we're still here → fail fast so the test shows a clear error
        raise TimeoutException(f"Could not click tab located by {locator} after retries")

    def list_all_publishers(self):
        """
        Ensure the 'All Publishers' view is active (click the tab if needed),
        then return a list of all publisher‐card WebElements.
        """
        # if there is an explicit "All Publishers" button/tab, click it:
        try:
            self.click(PublishersLocators.ALL_PUBLISHERS_BUTTON)
        except (TimeoutException, NoSuchElementException):
            # assume All is default
            pass

        # wait for cards to appear
        return self.finds(PublishersLocators.ALL_CARD)

    def list_publishers(self, view: str = ""):
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
        self.wait.until(EC.presence_of_element_located(PublishersLocators.GRID_CONTAINER))

        # return all the <a> publisher cards
        return self.finds(PublishersLocators.PUBLISHER_CARD)


    def open_publisher_by_index(self, index: int = 0, view: str = "") -> "PublisherDetailPage":
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
        return self.finds(PublishersLocators.USECASE_CARD)

    def open_usecase_by_index(self, index: int = 0):
        """
        Click the usecase-card link at position `index`,
        re-locating fresh so it can't go stale.
        """
        link_locator = (
            By.XPATH,
            f"({PublishersLocators.All_UC_Card[1]}//a)[{index+1}]"
        )
        self.wait.until(EC.element_to_be_clickable(link_locator)).click()
        return self