# pages/base_page.py
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

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
                except:
                    pass
            el.send_keys(Keys.DELETE)
            try:
                el.clear()
            except:
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
                for ch in text: el.send_keys(ch)
            else:
                el.send_keys(text)

            self.driver.execute_script("arguments[0].blur();", el)
            if (el.get_attribute("value") or "").strip() == text:
                return el

        raise AssertionError(f"Could not set value to '{text}'.")