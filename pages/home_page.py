# pages/home_page.py
from __future__ import annotations

import os
import time
from dotenv import load_dotenv
from typing import Union

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    WebDriverException
)
from selenium.webdriver import ActionChains
from pages.base_page import BasePage

# ─── Consumer‐flow imports (PLACE YOUR ORIGINAL IMPORTS HERE) ─────────────────────
#
from locators.homepage_locators import HomepageLocators
from pages.consumer.about_page import AboutPage
from pages.consumer.dataset_page import DatasetPage
from pages.consumer.publishers_page import PublishersPage
from pages.consumer.publisher_detail_page import PublisherDetailPage
from pages.consumer.sectors_page import SectorsPage
from pages.consumer.usecase_page import UseCasePage

# ────────────────────────────────────────────────────────────────────────────────

# ─── Provider‐flow imports ────────────────────────────────────────────────────────
from locators.provider.login_locators             import LoginLocators
from pages.provider.login_page                    import LoginPage
from pages.provider.provider_home_page             import ProviderHomePage
from locators.provider.provider_homepage_locators  import ProviderHomepageLocators
# ────────────────────────────────────────────────────────────────────────────────

# ─── Load environment variables once ───────────────────────────────────────────────
load_dotenv()
# BASE_URL      = os.getenv("BASE_URL")
# TEST_EMAIL    = os.getenv("TEST_EMAIL")
# TEST_PASSWORD = os.getenv("TEST_PASSWORD")
# ────────────────────────────────────────────────────────────────────────────────


class HomePage(BasePage):
    """


    Contains:
      1) Consumer‐flow navigation methods (e.g. go_to_about, go_to_all_data_page, etc.)
      2) A unified go_to_login(...) for consumer vs provider login
    """

    def __init__(self, driver, base_url):
        self.driver = driver
        self.url = base_url.rstrip("/") + "/"
        
    def load(self) -> None:
        """Navigate to the site root once."""
        self.driver.get(os.getenv("HOME_URL_DEV"))

    def is_loaded(self, timeout: int = 5) -> bool:
        """
        Returns True once the login‐form container is visible.
        We wait on the FORM locator.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, HomepageLocators.ICON))
            )
            return True
        except TimeoutException:
            return False
    
    # ─── Consumer‐flow navigation methods ───────────────────────────────────────────

    def go_to_about(self) -> AboutPage:
        btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, HomepageLocators.TAB_ABOUT))
        )
        btn.click()
        return AboutPage(self.driver)

    def go_to_all_data_page(self) -> DatasetPage:

        try:
            bann = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "cookieConsentAccept"))
            )
            bann.click()
        except:
            pass

        btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, HomepageLocators.TAB_DATASETS))
        )
        btn.click()
        return DatasetPage(self.driver)

    def go_to_publishers(self) -> PublishersPage:
        btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, HomepageLocators.TAB_PUBLISHERS))
        )
        btn.click()
        return PublishersPage(self.driver)

    def go_to_sectors(self) -> SectorsPage:
        btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, HomepageLocators.TAB_SECTORS))
        )
        btn.click()
        return SectorsPage(self.driver)

    def go_to_usecases(self) -> UseCasePage:
        btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, HomepageLocators.TAB_USECASES))
        )
        btn.click()
        return UseCasePage(self.driver)

    def is_icon_visible(self, timeout: int = 10) -> bool:
        """TC_HOM_01: Wait for the platform icon (logo) to be visible."""
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, HomepageLocators.ICON))
        )
        return True

    # ────────────────────────────────────────────────────────────────────────────────


    # ─── Provider‐flow login method ──────────────────────────────────────────────────

    def go_to_login(self, flow: str = "consumer", email: str|None = None, password: str|None = None):
        print("\n[STEP] Starting go_to_login (flow=%s)" % flow)
        self.logout()

        if flow.lower() == "provider":
            print("[WAIT] Checking if dashboard header is already visible")
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, ProviderHomepageLocators.HEADER))
                )
                print("[OK] Already logged in; ProviderHomePage visible")
                return ProviderHomePage(self.driver)
            except TimeoutException:
                print("[INFO] Not already logged in, continuing to login.")

        print("[WAIT] Waiting for LOGIN / SIGN UP button to be clickable")
        try:
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, LoginLocators.LOGIN_BUTTON))
            )
            print("[OK] Login button found, clicking…")
            login_btn.click()
            self.driver.save_screenshot(f"after_login_click_{int(time.time())}.png")
            print(f"[OK] Clicked LOGIN, current URL: {self.driver.current_url}")
        except Exception as e:
            print(f"[FAIL] Could not find or click login button: {e}")
            self.driver.save_screenshot('debug_login_fail.png')
            with open('debug_login_fail.html', 'w') as f:
                f.write(self.driver.page_source)
            raise

        print("[WAIT] Waiting for login form to appear (10s)")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, LoginLocators.FORM))
            )
            print("[OK] Login form is now visible")
        except TimeoutException as e:
            print("[FAIL] Login form never appeared after clicking LOGIN")
            self.driver.save_screenshot('debug_no_login_form.png')
            with open('debug_no_login_form.html', 'w') as f:
                f.write(self.driver.page_source)
            raise AssertionError("Tapped LOGIN / SIGN UP, but the login form never appeared.")

        login_page = LoginPage(self.driver)

        if flow.lower() == "provider":
            print("[ACTION] Logging in as provider (auto-fill)")
            # Use parameters if provided, else fallback
            email = email or os.getenv("TEST_EMAIL")
            password = password or os.getenv("TEST_PASSWORD")
            login_page.login(email, password)
            print("[WAIT] Waiting for ProviderHomePage header to appear (10s)")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, ProviderHomepageLocators.HEADER))
                )
                print("[OK] ProviderHomePage loaded after login")
            except TimeoutException as e:
                print("[FAIL] ProviderHomePage header did not appear after login")
                self.driver.save_screenshot('debug_post_login_fail.png')
                with open('debug_post_login_fail.html', 'w') as f:
                    f.write(self.driver.page_source)
                raise

            return ProviderHomePage(self.driver)

        return login_page

    # ────────────────────────────────────────────────────────────────────────────────

    # def test_login(driver, base_url, test_credentials):
    #     email, password = test_credentials
    #     home = HomePage(driver, base_url)
    #     home.go_to_login(flow="provider", email=email, password=password)

    def logout(self):
        try:
            # 1. Click the avatar/profile button
            avatar_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, HomepageLocators.LOGOUT_PROFILE_LOGO))
            )
            avatar_btn.click()

            # 2. Click "Log Out" in the dropdown
            logout_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, HomepageLocators.LOGOUT))
            )
            logout_btn.click()

            # 3. Optionally wait for login button to reappear (optional, adjust as needed)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//button[contains(.,'LOGIN') or contains(.,'Sign Up')]"))
            )
        except Exception as e:
            print("Logout not needed or failed:", e)

        # 4. Always clear cookies/storage for total isolation
        self.driver.delete_all_cookies()
        self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        self.driver.refresh()

