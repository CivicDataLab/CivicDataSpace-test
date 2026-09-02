# pages/consumer/bhashini_page.py
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from locators.consumer.bhashini_locators import BhashiniLocators
from pages.base_page import BasePage


class BhashiniWidgetPage(BasePage):
    """
    Presence checks for the Bhashini translation widget integration.

    Everything here waits on *presence*, not visibility: the injected
    <script> is never visible, and the plugin container can be an empty
    shell until the third-party bundle populates it.
    """

    def is_present(self, locator, timeout=None) -> bool:
        """True when at least one element matching `locator` is in the DOM."""
        wait = self.wait
        if timeout is not None:
            from selenium.webdriver.support.ui import WebDriverWait

            wait = WebDriverWait(self.driver, timeout)
        try:
            wait.until(EC.presence_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def has_plugin_script_by_src(self) -> bool:
        return self.is_present(BhashiniLocators.SCRIPT_BY_SRC)

    def has_plugin_script_by_id(self) -> bool:
        return self.is_present(BhashiniLocators.SCRIPT_BY_ID)

    def has_plugin_container(self) -> bool:
        return self.is_present(BhashiniLocators.PLUGIN_CONTAINER)

    def has_plugin_holder(self) -> bool:
        return self.is_present(BhashiniLocators.PLUGIN_HOLDER)

    def plugin_script_src(self) -> str:
        """The src of the injected plugin script (empty string if absent)."""
        elements = self.driver.find_elements(*BhashiniLocators.SCRIPT_BY_SRC)
        return elements[0].get_attribute("src") if elements else ""
