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
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(LoginLocators.FORM)
        )
        return True

    def login(self, email: str, password: str) -> ProviderHomePage:
        print("[WAIT] Waiting for email input field...")
        try:
            self.wait_with_timeout(10).until(
                EC.visibility_of_element_located(LoginLocators.EMAIL_INPUT)
            )
            print("[OK] Email input found")
        except Exception as e:
            print("[FAIL] Email input not found:", e)
            self.driver.save_screenshot('login_step_email_NOT_found.png')
            raise

        try:
            print("[ACTION] Filling email/password...")
            self.find(LoginLocators.EMAIL_INPUT).clear()
            self.find(LoginLocators.EMAIL_INPUT).send_keys(email)
            self.find(LoginLocators.PASSWORD_INPUT).clear()
            self.find(LoginLocators.PASSWORD_INPUT).send_keys(password)
            print("[OK] Filled email and password")
        except Exception as e:
            print("[FAIL] Could not fill credentials:", e)
            self.driver.save_screenshot('login_step_fill_credentials_FAIL.png')
            raise

        try:
            print("[ACTION] Clicking SIGN IN button...")
            self.find(LoginLocators.SIGNIN_BUTTON).click()
            print("[OK] SIGN IN clicked")
        except Exception as e:
            print("[FAIL] Could not click sign-in button:", e)
            self.driver.save_screenshot('login_step_signin_click_FAIL.png')
            raise

        try:
            print("[WAIT] Waiting for ProviderHomePage header after login (10s)")
            self.wait_with_timeout(10).until(
                EC.visibility_of_element_located(ProviderHomepageLocators.HEADER)
            )
            print("[OK] ProviderHomePage loaded after login")
        except Exception as e:
            print("[FAIL] ProviderHomePage header did not appear after login:", e)
            self.driver.save_screenshot('login_step_provider_homepage_header_FAIL.png')
            raise

        return ProviderHomePage(self.driver)
