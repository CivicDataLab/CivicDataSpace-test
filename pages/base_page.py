# pages/base_page.py
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class BasePage:
    def __init__(self, driver, timeout=15):
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

    def clear_and_type(self, locator, text, timeout=10, retries=2, slow=False):
        """Robustly set input value; handles React/Angular controlled inputs."""
        for _ in range(retries + 1):
            el = self.wait.until(EC.element_to_be_clickable(locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()

            # 1) Triple-click + Ctrl/Cmd+A + Delete + native clear
            ActionChains(self.driver).double_click(el).perform()
            for mod in (Keys.CONTROL, Keys.COMMAND):
                try:
                    el.send_keys(mod, "a")
                except Exception:
                    pass
            el.send_keys(Keys.DELETE)
            try:
                el.clear()
            except Exception:
                pass

            # 2) If still has text, backspace its length
            val = (el.get_attribute("value") or "")
            if val:
                el.send_keys(Keys.END)
                for _ in range(len(val)):
                    el.send_keys(Keys.BACKSPACE)

            # 3) If STILL not empty, use React-safe native setter + events
            if (el.get_attribute("value") or "").strip():
                self.driver.execute_script("""
                    const e = arguments[0];
                    const desc = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
                    if (desc && desc.set) desc.set.call(e, '');
                    else e.value = '';
                    e.dispatchEvent(new Event('input', {bubbles:true}));
                    e.dispatchEvent(new Event('change', {bubbles:true}));
                """, el)

            # Type and verify
            if slow:
                for ch in text:
                    el.send_keys(ch)
            else:
                el.send_keys(text)

            self.driver.execute_script("arguments[0].blur();", el)
            if (el.get_attribute("value") or "").strip() == text:
                return el

        raise AssertionError(f"Could not set value to '{text}'.")

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
            self.driver.execute_script("arguments[0].click();", opt)

        import time
        time.sleep(0.5)

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
        Primary: send_keys after removing display:none (triggers real browser/React events + server upload).
        Fallback: JavaScript DataTransfer (updates client-side state only).
        """
        import os, time, base64
        from selenium.webdriver.common.by import By

        assert os.path.isfile(path_to_file), f"File does not exist: {path_to_file}"
        abs_path = os.path.abspath(path_to_file)
        file_name = os.path.basename(abs_path)
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}
        mime_type = mime_map.get(ext, "application/octet-stream")

        input_el = self.driver.find_element(By.XPATH, "//input[@type='file']")

        # Remove display:none so ChromeDriver can interact with the file input.
        # ChromeDriver uses CDP DOM.setFileInputFiles which triggers real browser events
        # (including React's synthetic onChange), enabling server-side upload.
        self.driver.execute_script("arguments[0].removeAttribute('style');", input_el)
        time.sleep(0.2)

        try:
            input_el.send_keys(abs_path)
            time.sleep(2)
            files_len = self.driver.execute_script("return arguments[0].files.length", input_el)
            if files_len > 0:
                return self
        except Exception:
            pass

        # Fallback: JavaScript DataTransfer (updates React state client-side)
        with open(abs_path, "rb") as f:
            file_b64 = base64.b64encode(f.read()).decode()

        self.driver.execute_script("""
            var b64 = arguments[0], name = arguments[1], mime = arguments[2], input = arguments[3];
            try {
                var bytes = atob(b64);
                var arr = new Uint8Array(bytes.length);
                for (var i = 0; i < bytes.length; i++) { arr[i] = bytes.charCodeAt(i); }
                var blob = new Blob([arr], {type: mime});
                var file = new File([blob], name, {type: mime});
                var dt = new DataTransfer();
                dt.items.add(file);
                Object.defineProperty(input, 'files', {writable: true, configurable: true, value: dt.files});
                var event = new Event('change', {bubbles: true, cancelable: false});
                input.dispatchEvent(event);
                return input.files.length;
            } catch(e) { return 'error: ' + e; }
        """, file_b64, file_name, mime_type, input_el)
        time.sleep(2)
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

    # ── Autosave Utility ───────────────────────────────────────────────────────

    def wait_for_autosave(self, trigger_blur=True, timeout=15):
        """
        Wait for the editor autosave cycle to commit pending changes.

        Blurs the currently focused element via JavaScript to fire its onBlur
        handler (body.click() does not reliably blur inputs in Chrome), then
        waits for the 'Saving...' indicator to appear and resolve.
        Falls back to a generous sleep if the indicator is too fast to catch.
        """
        import time as _time
        from selenium.webdriver.common.by import By

        if trigger_blur:
            try:
                # JS blur reliably triggers React's onBlur; body.click() does not
                # move focus away from focusable elements in Chrome.
                self.driver.execute_script(
                    "var el = document.activeElement;"
                    "if (el && el.tagName !== 'BODY') { el.blur(); }"
                )
            except Exception:
                pass

        saving_locator = (By.XPATH, "//*[normalize-space(text())='Saving...']")

        try:
            # Poll at 100ms to catch brief Saving... indicator (default is 500ms)
            WebDriverWait(self.driver, 5, poll_frequency=0.1).until(
                EC.presence_of_element_located(saving_locator)
            )
            # Save in progress — wait until it finishes
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(saving_locator)
            )
            _time.sleep(0.3)
        except TimeoutException:
            # Saving... didn't appear — either already saved or save was too fast
            # to catch. Add a generous margin to ensure the network round-trip
            # completes before navigating away.
            _time.sleep(4)

        return self
