# tests/consumer/functional/test_con_consumer_login_needed.py

import os
import pytest
from selenium.webdriver.common.by import By
from locators.provider.login_locators import LoginLocators
from pages.home_page      import HomePage
from pages.provider.login_page import LoginPage

@pytest.mark.functional
def test_con_001_consumer_login(driver, base_url):
    driver.delete_all_cookies()
    home = HomePage(driver, base_url)
    home.load()

    # 1) Click LOGIN / SIGN UP and get back a LoginPage (no auto‐redirect).
    login_page = home.go_to_login(flow="consumer")
    assert isinstance(login_page, LoginPage)

    # 2) Fill in the consumer test creds from .env or other fixture
    email = os.getenv("TEST_EMAIL_1")
    pw    = os.getenv("TEST_PASSWORD_1")
    dashboard_page = login_page.login(email, pw)

    # 3) Assert dashboard page after login loaded 
    assert dashboard_page.is_header_visible()
