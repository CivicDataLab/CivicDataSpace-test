import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC
from pages.home_page               import HomePage
from pages.provider.login_page     import LoginPage
from pages.provider.provider_home_page  import ProviderHomePage
from locators.provider.provider_homepage_locators import ProviderHomepageLocators
from locators.provider.login_locators import LoginLocators



@pytest.mark.smoke
def test_prv_001_login_smoke(driver, base_url):
    # Step 0: ensure a clean session
    home = HomePage(driver, base_url)
    home.load()

    # Step 1: click LOGIN / SIGN UP and expect a LoginPage
    prov_home = home.go_to_login(flow="provider")
    # Assert that go_to_login actually returned a ProviderHomePage
    assert isinstance(prov_home, ProviderHomePage), "Did not land on ProviderHomePage"

    # Optionally, verify some element on ProviderHomePage is visible:
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, ProviderHomepageLocators.HEADER))
    )
    assert prov_home.is_header_visible()