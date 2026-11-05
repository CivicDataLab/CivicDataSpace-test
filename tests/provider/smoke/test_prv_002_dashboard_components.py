# tests/provider/smoke/test_prv_002_dashboard_components.py

import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.organizations_page import OrganizationsPage
from locators.provider.provider_homepage_locators import ProviderHomepageLocators
from locators.provider.my_dashboard_locators import MyDashboardLocators
from locators.provider.org_locators import OrgLocators


def _login_as_provider(driver, base_url, test_credentials) -> ProviderHomePage:
    driver.delete_all_cookies()
    email, password = test_credentials
    home = HomePage(driver, base_url)
    try:
        if not home.is_loaded():
            home.load()
    except Exception:
        pass
    return home.go_to_login(flow="provider", email=email, password=password)


@pytest.mark.smoke
def test_prv_002_01_user_dashboard_header_visible(driver, base_url, test_credentials):
    """User Dashboard heading is visible after login."""
    prov_home = _login_as_provider(driver, base_url, test_credentials)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after login, got {type(prov_home)}"
    )
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(ProviderHomepageLocators.HEADER)
    )


@pytest.mark.smoke
def test_prv_002_02_dashboard_cards_visible(driver, base_url, test_credentials):
    """'My Dashboard' and 'Organizations' cards are both visible on the landing page."""
    prov_home = _login_as_provider(driver, base_url, test_credentials)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after login, got {type(prov_home)}"
    )
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(ProviderHomepageLocators.CARD_MY_DASH)
    )
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(ProviderHomepageLocators.CARD_ORGANIZATIONS)
    )


@pytest.mark.smoke
def test_prv_002_03_ind_sidebar_nav_visible(driver, base_url, test_credentials):
    """All sidebar nav items are visible on the Individual (My Dashboard) view."""
    prov_home = _login_as_provider(driver, base_url, test_credentials)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after login, got {type(prov_home)}"
    )
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        f"Expected MyDashboardPage, got {type(my_dash)}"
    )

    sidebar_items = [
        ("Datasets",       MyDashboardLocators.SIDEBAR_DATASETS),
        ("UseCases",       MyDashboardLocators.USECASES_NAV_LINK),
        ("Collaboratives", MyDashboardLocators.COLLABORATIVES_NAV_LINK),
        ("AI Models",      MyDashboardLocators.AI_MODELS_NAV_LINK),
        ("Profile",        MyDashboardLocators.PROFILE_NAV_LINK),
    ]
    for label, locator in sidebar_items:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(locator),
            f"Individual dashboard sidebar item not visible: {label}"
        )


@pytest.mark.smoke
def test_prv_002_04_org_sidebar_nav_visible(driver, base_url, test_credentials, writable_org):
    """All sidebar nav items are visible on the Org dashboard after selecting an org."""
    prov_home = _login_as_provider(driver, base_url, test_credentials)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after login, got {type(prov_home)}"
    )
    org_page = prov_home.goto_organizations()
    assert isinstance(org_page, OrganizationsPage), (
        f"Expected OrganizationsPage, got {type(org_page)}"
    )
    org_page.select_org(writable_org)

    sidebar_items = [
        ("Datasets",       OrgLocators.SIDEBAR_DATASETS),
        ("UseCases",       OrgLocators.USECASES_NAV_LINK),
        ("Collaboratives", OrgLocators.COLLABORATIVES_NAV_LINK),
        ("AI Models",      OrgLocators.AI_MODELS_NAV_LINK),
        ("Profile",        OrgLocators.PROFILE_NAV_LINK),
    ]
    for label, locator in sidebar_items:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(locator),
            f"Org dashboard sidebar item not visible: {label}"
        )
