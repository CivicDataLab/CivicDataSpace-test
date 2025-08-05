# pages/provider/login_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.base_page import BasePage
from pages.provider.provider_home_page import ProviderHomePage
from locators.provider.login_locators import LoginLocators
from locators.provider.provider_homepage_locators import ProviderHomepageLocators

class LoginPage(BasePage):
    """POM for the Keycloak login screen."""

    def is_loaded(self, timeout: int = 10) -> bool:
        """
        Returns True once the login‐form container is visible.
        We wait on the FORM locator.
        """
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, LoginLocators.FORM))
        )
        return True

    def login(self, email: str, password: str) -> ProviderHomePage:
        """
        Fill email/password and submit.  Then return the ProviderHomePage
        (once its header appears).
        """
        # 1) wait for email input to appear
        WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, LoginLocators.EMAIL_INPUT))
        )

        # 2) fill in email + password
        self.find((By.XPATH, LoginLocators.EMAIL_INPUT)).clear()
        self.find((By.XPATH, LoginLocators.EMAIL_INPUT)).send_keys(email)

        self.find((By.XPATH, LoginLocators.PASSWORD_INPUT)).clear()
        self.find((By.XPATH, LoginLocators.PASSWORD_INPUT)).send_keys(password)

        # 3) click “Sign In”
        self.find((By.XPATH, LoginLocators.SIGNIN_BUTTON)).click()

        # 4) wait for the ProviderHomePage header to confirm successful login
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, ProviderHomepageLocators.HEADER)
            )
        )
        return ProviderHomePage(self.driver)
