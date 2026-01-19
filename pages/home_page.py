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
        super().__init__(driver)  # Initialize BasePage with self.wait
        self.url = base_url.rstrip("/") + "/"
        
    def load(self) -> None:
        """Navigate to the site root once."""
        self.driver.get(os.getenv("HOME_URL_DEV"))
        # Wait for page to start loading and initial content to appear
        time.sleep(2)
        # Aggressively dismiss tour popup
        self.dismiss_tour_popup()
        # Double-check and dismiss again if it reappeared
        self.dismiss_tour_popup()

    def dismiss_tour_popup(self, timeout: int = 3) -> None:
        """
        Dismiss the tour popup using multiple strategies.
        Safe to call even if popup doesn't exist.
        """
        try:
            skip_btn = self.wait_with_timeout(timeout).until(
                EC.presence_of_element_located(HomepageLocators.SKIP_TOUR_BUTTON)
            )

            # Try JavaScript click first (most reliable)
            try:
                self.driver.execute_script("arguments[0].click();", skip_btn)
                time.sleep(0.5)
            except Exception:
                # Fallback to regular click
                try:
                    skip_btn.click()
                    time.sleep(0.5)
                except Exception:
                    pass

            # If popup still exists, forcefully remove it from DOM
            try:
                popup_elements = self.driver.find_elements(*HomepageLocators.SKIP_TOUR_BUTTON)
                if popup_elements:
                    self.driver.execute_script("""
                        var skipBtn = arguments[0];
                        var modal = skipBtn.closest('div[role="dialog"]') ||
                                    skipBtn.closest('div[class*="modal"]') ||
                                    skipBtn.closest('div[class*="Modal"]') ||
                                    skipBtn.parentElement.parentElement;
                        if (modal) modal.remove();
                        skipBtn.remove();
                    """, popup_elements[0])
                    time.sleep(0.5)
            except Exception:
                pass

            time.sleep(0.5)

        except (TimeoutException, Exception):
            # Popup doesn't exist or other non-critical error
            pass

    def is_loaded(self, timeout: int = 5) -> bool:
        """
        Returns True once the login‐form container is visible.
        We wait on the FORM locator.
        """
        try:
            self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(HomepageLocators.ICON)
            )
            return True
        except TimeoutException:
            return False
    
    # ─── Consumer‐flow navigation methods ───────────────────────────────────────────

    def go_to_about(self) -> AboutPage:
        self.dismiss_tour_popup()  # Ensure popup is gone before clicking
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(HomepageLocators.TAB_ABOUT)
        )
        btn.click()

        # Wait for URL to change to about page
        self.wait_with_timeout(10).until(
            lambda driver: "/about" in driver.current_url
        )
        time.sleep(1)  # Brief pause for page to start rendering

        return AboutPage(self.driver)

    def go_to_all_data_page(self) -> DatasetPage:
        self.dismiss_tour_popup()  # Ensure popup is gone before clicking

        try:
            bann = self.wait_with_timeout(10).until(
                EC.element_to_be_clickable((By.ID, "cookieConsentAccept"))
            )
            bann.click()
        except TimeoutException:
            pass

        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(HomepageLocators.TAB_DATASETS)
        )
        btn.click()

        # Wait for URL to change to datasets page
        self.wait_with_timeout(10).until(
            lambda driver: "/datasets" in driver.current_url
        )
        time.sleep(1)  # Brief pause for page to start rendering

        return DatasetPage(self.driver)

    def go_to_publishers(self) -> PublishersPage:
        self.dismiss_tour_popup()  # Ensure popup is gone before clicking
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(HomepageLocators.TAB_PUBLISHERS)
        )
        btn.click()

        # Wait for URL to change to publishers page
        self.wait_with_timeout(10).until(
            lambda driver: "/publishers" in driver.current_url
        )
        time.sleep(1)  # Brief pause for page to start rendering

        return PublishersPage(self.driver)

    def go_to_sectors(self) -> SectorsPage:
        self.dismiss_tour_popup()  # Ensure popup is gone before clicking
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(HomepageLocators.TAB_SECTORS)
        )
        btn.click()

        # Wait for URL to change to sectors page
        self.wait_with_timeout(10).until(
            lambda driver: "/sectors" in driver.current_url
        )
        time.sleep(1)  # Brief pause for page to start rendering

        return SectorsPage(self.driver)

    def go_to_usecases(self) -> UseCasePage:
        self.dismiss_tour_popup()  # Ensure popup is gone before clicking
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(HomepageLocators.TAB_USECASES)
        )
        btn.click()

        # Wait for URL to change to usecases page
        self.wait_with_timeout(10).until(
            lambda driver: "/usecases" in driver.current_url
        )
        time.sleep(1)  # Brief pause for page to start rendering

        return UseCasePage(self.driver)

    def is_icon_visible(self, timeout: int = 10) -> bool:
        """TC_HOM_01: Wait for the platform icon (logo) to be visible."""
        self.dismiss_tour_popup()  # Ensure popup doesn't block visibility check
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(HomepageLocators.ICON)
        )
        return True

    # ────────────────────────────────────────────────────────────────────────────────


    # ─── Provider‐flow login method ──────────────────────────────────────────────────

    def go_to_login(self, flow: str = "consumer", email: str|None = None, password: str|None = None):
        print("\n[STEP] Starting go_to_login (flow=%s)" % flow)
        self.logout()

        # Dismiss tour popup if it's blocking the login button
        self.dismiss_tour_popup()

        if flow.lower() == "provider":
            print("[WAIT] Checking if dashboard header is already visible")
            try:
                self.wait.until(
                    EC.visibility_of_element_located(ProviderHomepageLocators.HEADER)
                )
                print("[OK] Already logged in; ProviderHomePage visible")
                return ProviderHomePage(self.driver)
            except TimeoutException:
                print("[INFO] Not already logged in, continuing to login.")

        print("[WAIT] Waiting for LOGIN / SIGN UP button to be clickable")
        try:
            login_btn = self.wait_with_timeout(10).until(
                EC.element_to_be_clickable(LoginLocators.LOGIN_BUTTON)
            )
            print("[OK] Login button found, clicking…")
            login_btn.click()
            print(f"[OK] Clicked LOGIN, current URL: {self.driver.current_url}")
        except Exception as e:
            print(f"[FAIL] Could not find or click login button: {e}")
            self.driver.save_screenshot('debug_login_fail.png')
            with open('debug_login_fail.html', 'w') as f:
                f.write(self.driver.page_source)
            raise

        print("[WAIT] Waiting for login form to appear (10s)")
        try:
            self.wait_with_timeout(10).until(
                EC.visibility_of_element_located(LoginLocators.FORM)
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
                self.wait_with_timeout(10).until(
                    EC.visibility_of_element_located(ProviderHomepageLocators.HEADER)
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
            avatar_btn = self.wait.until(
                EC.element_to_be_clickable(HomepageLocators.LOGOUT_PROFILE_LOGO)
            )
            avatar_btn.click()

            # 2. Click "Log Out" in the dropdown
            logout_btn = self.wait.until(
                EC.element_to_be_clickable(HomepageLocators.LOGOUT)
            )
            logout_btn.click()

            # 3. Optionally wait for login button to reappear (optional, adjust as needed)
            self.wait_with_timeout(10).until(
                EC.visibility_of_element_located((By.XPATH, "//button[contains(.,'LOGIN') or contains(.,'Sign Up')]"))
            )
        except Exception as e:
            print("Logout not needed or failed:", e)

        # 4. Always clear cookies/storage for total isolation
        self.driver.delete_all_cookies()
        self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        self.driver.refresh()

