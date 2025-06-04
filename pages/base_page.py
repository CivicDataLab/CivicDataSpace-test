# pages/base_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver, timeout=10):
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
