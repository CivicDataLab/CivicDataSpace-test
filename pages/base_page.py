# pages/base_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys

class BasePage:
    def __init__(self, driver, timeout=5):
        self.driver = driver
        self.wait   = WebDriverWait(driver, timeout)

    def visit(self, url):
        self.driver.get(url)

    def find(self, by_locator):
        return self.wait.until(EC.visibility_of_element_located(by_locator))

    def finds(self, by_locator):
        return self.wait.until(EC.presence_of_all_elements_located(by_locator))

    def click(self, by_locator):
        elem = self.wait.until(EC.element_to_be_clickable(by_locator))
        elem.click()
        return elem

    # ── Text Input Utilities ──────────────────────────────────────────────────

    def clear_and_type(self, locator, text):
        """
        Clear field and type text using triple-click selection for React forms.
        Triple-click selects all text, then typing replaces the selection.
        """
        import time
        from selenium.webdriver.common.action_chains import ActionChains

        element = self.wait.until(EC.visibility_of_element_located(locator))

        # Triple-click to select all text (more reliable than Ctrl+A for React)
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click().click().click().perform()
        time.sleep(0.1)

        # Type the new text (replaces the selection)
        element.send_keys(text)

        return element

    def type_text(self, locator, text):
        """Type text without clearing"""
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.send_keys(text)
        return element

    def clear_field(self, locator):
        """Clear input field"""
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.clear()
        return element

    # ── Dropdown & Selection Utilities ────────────────────────────────────────

    def select_dropdown_by_text(self, locator, text):
        """Select from native <select> dropdown by visible text"""
        from selenium.webdriver.support.ui import Select
        element = self.wait.until(EC.presence_of_element_located(locator))
        Select(element).select_by_visible_text(text)
        return element

    def select_combobox_option(self, input_locator, option_text):
        """
        Generic combobox selection - click input, type, select option, close dropdown.
        Works with React/custom dropdowns that aren't native <select> elements.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.common.exceptions import ElementClickInterceptedException

        combo = self.wait.until(EC.element_to_be_clickable(input_locator))
        combo.click()
        combo.clear()
        combo.send_keys(option_text)

        # Wait for dropdown option to appear
        xpath = f"//div[@role='option' and normalize-space(.)='{option_text}']"
        opt = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

        try:
            opt.click()
        except ElementClickInterceptedException:
            # Fallback to JavaScript click if regular click is intercepted
            self.driver.execute_script("arguments[0].click();", opt)

        # Close dropdown with Escape key
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    # ── Wait Utilities ─────────────────────────────────────────────────────────

    def wait_for_invisibility(self, locator, timeout=None):
        """Wait for element to become invisible"""
        wait = WebDriverWait(self.driver, timeout) if timeout else self.wait
        return wait.until(EC.invisibility_of_element_located(locator))

    def wait_for_url_contains(self, text, timeout=10):
        """Wait for URL to contain specific text"""
        return WebDriverWait(self.driver, timeout).until(
            lambda d: text in d.current_url
        )

    def wait_with_timeout(self, timeout):
        """Create a one-off wait with custom timeout"""
        return WebDriverWait(self.driver, timeout)

    # ── File Upload Utility ────────────────────────────────────────────────────

    def upload_file_to_dropzone(self, path_to_file, dropzone_class="DropZone-module_DropZone__xD9-6"):
        """
        Standard file upload to React DropZone component.
        Handles making hidden file input visible and sending file path.
        """
        import os
        from selenium.webdriver.common.by import By

        assert os.path.isfile(path_to_file), f"File does not exist: {path_to_file}"

        dropzone = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, dropzone_class))
        )
        dropzone.click()

        input_el = self.driver.find_element(By.XPATH, "//input[@type='file']")
        self.driver.execute_script("arguments[0].style.display = 'block';", input_el)
        input_el.send_keys(path_to_file)
        return self

    # ── Element State Utilities ────────────────────────────────────────────────

    def get_attribute(self, locator, attribute_name):
        """Get attribute value from element"""
        element = self.wait.until(EC.presence_of_element_located(locator))
        return element.get_attribute(attribute_name)

    def get_text(self, locator):
        """Get text content from element"""
        element = self.wait.until(EC.visibility_of_element_located(locator))
        return element.text.strip()

    def is_visible(self, locator, timeout=5):
        """
        Check if element is visible within timeout period.
        Returns True if visible, False if not found or not visible.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    # ── Advanced Interaction Utilities ─────────────────────────────────────────

    def scroll_to_element(self, locator):
        """Scroll element into view (center of viewport)"""
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            element
        )
        return element

    def js_click(self, locator):
        """
        Click element via JavaScript (bypasses intercepted clicks).
        Use when standard click() fails due to overlays or animations.
        """
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].click();", element)
        return element
