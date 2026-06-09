# pages/provider/collaboratives_list_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from pages.provider.create_collaborative_page import CreateCollaborativePage
from locators.provider.collaboratives_list_page_locators import CollaborativesListPageLocators
from locators.provider.create_collaborative_locators import CreateCollaborativeLocators


class CollaborativesListPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver)  # Initialize BasePage with self.wait

    def is_loaded(self):
        return self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON)
        )

    def click_add_new_collaborative(self):
        """
        Click the "Add New Collaborative" button and wait for the create collaborative form to load.

        Returns:
            CreateCollaborativePage instance after the form has loaded
        """
        import time
        from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

        url_before = self.driver.current_url

        # Use JavaScript to find the deepest element with "Add New Collaborative" text
        # The broad XPath locator matches <html>, so JS is needed to find the actual clickable span
        js_element = self.driver.execute_script("""
            var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
            var found = null;
            while (walker.nextNode()) {
                var el = walker.currentNode;
                if (el.textContent.trim() === 'Add New Collaborative') {
                    found = el;  // keep going to find deepest match
                }
            }
            if (found) {
                return {tag: found.tagName, cls: found.className, el: found};
            }
            return null;
        """)

        # Try Selenium locators for reliable clicking (element_to_be_clickable ensures interactable)
        # NOTE: broad locator is intentionally excluded here (it matches <html>, not the button)
        button = None
        for locator in [
            (By.XPATH, "//span[contains(@class,'Button-module_removeUnderline') and normalize-space()='Add New Collaborative']"),
            (By.XPATH, "//span[normalize-space()='Add New Collaborative']"),
            (By.XPATH, "//a[contains(normalize-space(.), 'Add New Collaborative')]"),
            (By.XPATH, "//button[contains(normalize-space(.), 'Add New Collaborative')]"),
            (By.XPATH, "//*[normalize-space()='Add New Collaborative' and not(self::html) and not(self::body) and not(self::div[@id='__next'])]"),
        ]:
            try:
                button = self.wait_with_timeout(3).until(EC.element_to_be_clickable(locator))
                break
            except TimeoutException:
                continue

        # Fallback: use the JS-found element directly
        if not button and js_element and js_element.get('el'):
            button = js_element['el']

        if not button:
            raise TimeoutException("Could not find 'Add New Collaborative' button to click")

        try:
            button.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", button)

        # Wait for URL to change (confirms navigation happened)
        try:
            self.wait_with_timeout(10).until(lambda d: d.current_url != url_before)
        except TimeoutException:
            pass  # URL may not change if already on create form

        # Wait for the Collaborative creation form to load — try multiple indicators
        form_locators = [
            (By.XPATH, "//input[@name='platformUrl']"),                       # Platform URL named input
            CreateCollaborativeLocators.COLLABORATIVE_SUMMARY_INPUT,          # Quill editor
            CreateCollaborativeLocators.DETAILS_TAB,                          # "Collaborative Details" tab button
            (By.XPATH, "//label[normalize-space()='Summary *']"),             # Summary label
            (By.XPATH, "//*[@contenteditable='true']"),                       # Any rich text editor
            (By.XPATH, "//button[normalize-space()='Next']"),                 # Next button (wizard nav)
        ]
        loaded = False
        for locator in form_locators:
            try:
                self.wait_with_timeout(15).until(EC.visibility_of_element_located(locator))
                loaded = True
                break
            except TimeoutException:
                continue

        if not loaded:
            raise TimeoutException(
                msg=f"Timed out waiting for Collaborative creation form to load. URL={self.driver.current_url}"
            )

        return CreateCollaborativePage(self.driver)
