# pages/consumer/publisher_detail_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage
from locators.consumer.publisher_detail_locators import PublisherDetailLocators

class PublisherDetailPage(BasePage):
    def __init__(self, driver, publisher_type: str = "all", timeout: int = 10):
        super().__init__(driver, timeout)
        self.publisher_type = publisher_type

    def list_usecases(self):
        """
        Wait for at least one use-case card, then return all of them.
        """
        # wait for the grid
        self.wait.until(EC.presence_of_element_located((By.XPATH, PublisherDetailLocators.USECASE_GRID)))
        # return all the links
        return self.finds((By.XPATH, PublisherDetailLocators.USECASE_CARD))

    def open_usecase_by_index(self, index: int = 0):
        """
        Click the Nth use-case <a> and return self (or a UseCaseDetailPage).
        """
        cards = self.list_usecases()
        if len(cards) <= index:
            raise AssertionError(f"No use-case at index {index} (found {len(cards)})")
        try:
            cards[index].click()
        except TimeoutException:
            # artifact dump on failure
            self.driver.save_screenshot("open_usecase_fail.png")
            with open("open_usecase_fail.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise
        return self
