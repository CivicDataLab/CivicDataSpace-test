# tests/test_homepage.py

import logging
import os
import pytest
from dotenv import load_dotenv

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from locators.consumer.locators import Locators

load_dotenv()

# ─── LOGGER SETUP ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)

# driver fixture is provided by conftest.py

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")


def load_homepage(driver):
    logger.info("Loading homepage: %s", BASE_URL)
    driver.get(BASE_URL)

# ─── HELPER: wait + screenshot on failure ────────────────────────────────────────
def wait_and_capture(driver, tc_id, by, locator, condition=EC.visibility_of_element_located, timeout=10):
    """
    Waits for `condition((by, locator))`. On timeout, saves screenshot + HTML, then fails.
    """
    try:
        return WebDriverWait(driver, timeout).until(condition((by, locator)))
    except TimeoutException:
        screenshot = f"{tc_id}_failure.png"
        html_dump   = f"{tc_id}_failure.html"
        driver.save_screenshot(screenshot)
        with open(html_dump, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        pytest.fail(f"{tc_id} failed: '{locator}' not satisfied by {condition.__name__}. "
                    f"See {screenshot}")

# ─── SMOKE TESTS ────────────────────────────────────────────────────────────────

@pytest.mark.smoke
def test_TC_HOM_01_icon_visible(driver):
    """Verify homepage icon is visible on page load"""
    load_homepage(driver)
    icon = wait_and_capture(driver, "TC_HOM_01", *Locators.ICON)
    assert icon.is_displayed()


@pytest.mark.smoke
def test_TC_HOM_15_privacy_link_in_footer(driver):
    """Footer exposes a Privacy link pointing at /privacy.

    Covers DataSpaceFrontend#447, which added the link to MainFooter. The href
    is conditional there (absolute platform URL on a collaborative subdomain,
    relative /privacy otherwise); this asserts the non-subdomain branch, which
    is what dev serves.
    """
    load_homepage(driver)
    link = wait_and_capture(driver, "TC_HOM_15", *Locators.PRIVACY_LINK)
    assert link.is_displayed(), "Privacy link is not visible in the footer"

    href = link.get_attribute("href") or ""
    assert href.rstrip("/").endswith("/privacy"), (
        f"Privacy link points at {href!r}, expected a URL ending in /privacy"
    )


@pytest.mark.smoke
def test_TC_HOM_16_privacy_page_renders(driver):
    """Following the footer Privacy link lands on a real privacy page.

    The link existing is not enough — a link to a 404 would still satisfy
    TC_HOM_15. This follows it and checks the destination actually rendered
    policy content rather than an error page.
    """
    load_homepage(driver)
    link = wait_and_capture(driver, "TC_HOM_15", *Locators.PRIVACY_LINK)
    driver.get(link.get_attribute("href"))

    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    assert "/privacy" in driver.current_url, (
        f"Expected to land on the privacy page, got {driver.current_url}"
    )
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "privacy" in body.lower(), "Privacy page rendered no privacy content"
    assert "404" not in body and "not found" not in body.lower(), (
        "Privacy link led to a 404 / not-found page"
    )

@pytest.mark.smoke
def test_TC_HOM_02_image_renders(driver):
    """Verify homepage image renders without error"""
    load_homepage(driver)
    img = wait_and_capture(driver, "TC_HOM_02", *Locators.IMAGE)
    # The hero is a ~1.5MB lazy-loaded SVG: it is visible before it finishes loading.
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return arguments[0].complete && arguments[0].naturalWidth > 0", img),
        message="TC_HOM_02: hero image never finished loading (naturalWidth stayed 0)",
    )

@pytest.mark.smoke
def test_TC_HOM_03_search_bar_present(driver):
    """Verify search bar is visible"""
    load_homepage(driver)
    bar = wait_and_capture(driver, "TC_HOM_03", *Locators.SEARCH_BAR)
    assert bar.is_displayed()

@pytest.mark.smoke
def test_TC_HOM_04_search_button_clickable(driver):
    """Verify search button is clickable (no crash on empty click)"""
    load_homepage(driver)
    btn = wait_and_capture(driver, "TC_HOM_04", *Locators.SEARCH_BUTTON, condition=EC.element_to_be_clickable)
    assert btn.is_displayed()

@pytest.mark.smoke
def test_TC_HOM_05_recent_datasets_btn(driver):
    """Explore All Datasets button exists"""
    load_homepage(driver)
    btn = wait_and_capture(driver, "TC_HOM_05", *Locators.RECENT_DATASETS_BTN)
    assert btn.is_displayed()

@pytest.mark.smoke
def test_TC_HOM_06_explore_sectors_btn(driver):
    """Explore All Sectors button is present"""
    load_homepage(driver)
    btn = wait_and_capture(driver, "TC_HOM_06", *Locators.EXPLORE_SECTORS_BTN)
    assert btn.is_displayed()

@pytest.mark.smoke
def test_TC_HOM_07_about_link(driver):
    """Footer About Us link is visible"""
    load_homepage(driver)
    link = wait_and_capture(driver, "TC_HOM_07", *Locators.ABOUT_LINK)
    assert link.is_displayed()

@pytest.mark.smoke
def test_TC_HOM_09_contact_section(driver):
    """Contact Us section is present"""
    load_homepage(driver)
    sec = wait_and_capture(driver, "TC_HOM_09", *Locators.CONTACT_SECTION)
    assert sec.is_displayed()

# To be added once the social media links are visible.
# @pytest.mark.parametrize("locator,tc_id", [
#     (Locators.TWITTER_ICON,  "TC_HOM_10"),
#     (Locators.LINKEDIN_ICON, "TC_HOM_11"),
#     (Locators.FACEBOOK_ICON, "TC_HOM_12"),
#     (Locators.GITHUB_ICON,   "TC_HOM_13"),
# ])
# def test_TC_HOM_10_to_13_social_icons(driver, locator, tc_id):
#     """Verify all social media icons are visible"""
#     load_homepage(driver)
#     icon_link = wait_and_capture(driver, tc_id, By.XPATH, locator, condition=EC.element_to_be_clickable)
#     assert icon_link.is_displayed(), f"{tc_id} failed: link not displayed"
'''

def test_TC_HOM_14_cdl_redirect(driver):
    """CDL redirect element present"""
    load_homepage(driver)
    link = wait_and_capture(driver, "TC_HOM_14", By.XPATH, Locators.CDL_REDIRECT_ELEMENT)
    href = link.get_attribute("href")
    assert href.startswith("https://www.civicdatalab.in/"), f"Unexpected href: {href}"

# ─── DATASET TAB TESTS ─────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def dataset_page(driver):
    load_homepage(driver)
    tab = wait_and_capture(
        driver, "SETUP_DS_TAB", By.XPATH, Locators.DATASET_TAB,
        condition=EC.element_to_be_clickable
    )
    tab.click()
    return driver

def test_TC_DS_01_search_field_visible(dataset_page):
    bar = wait_and_capture(dataset_page, "TC_DS_01", By.XPATH, Locators.DATASET_SEARCH_FIELD)
    assert bar.is_displayed()

def test_TC_DS_02_sector_filter_dropdown(dataset_page):
    btn = wait_and_capture(dataset_page, "TC_DS_02", By.XPATH, Locators.DATASET_FILTER_RESET_BUTTON)
    btn.click()
    sd = wait_and_capture(dataset_page, "TC_DS_02", By.XPATH, Locators.DATASET_SECTOR_DROPDOWN)
    assert sd.is_displayed()

def test_TC_DS_03_tags_filter_dropdown(dataset_page):
    btn = wait_and_capture(dataset_page, "TC_DS_03", By.XPATH, Locators.DATASET_FILTER_RESET_BUTTON)
    btn.click()
    td = wait_and_capture(dataset_page, "TC_DS_03", By.XPATH, Locators.DATASET_TAGS_DROPDOWN)
    assert td.is_displayed()

def test_TC_DS_04_toggle_view_options(dataset_page):
    grid = wait_and_capture(dataset_page, "TC_DS_04", By.XPATH, Locators.DATASET_TOGGLE_GRID)
    lst  = wait_and_capture(dataset_page, "TC_DS_04", By.XPATH, Locators.DATASET_TOGGLE_LIST)
    assert grid.is_displayed() and lst.is_displayed() and grid != lst

def test_TC_DS_05_dataset_cards_render(dataset_page):
    """TC_DS_04: Dataset cards are rendered on the Dataset tab"""
    # wait up to 10s for *all* cards to be present in the DOM
    cards = WebDriverWait(dataset_page, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, Locators.DATASET_CARD))
    )

    count = len(cards)
    assert count > 0, (
        f"TC_DS_04 failed: expected >0 dataset cards, but found {count}. "
        "Check your `Locators.DATASET_CARD` XPath."
    )

def test_TC_DS_06_view_details_links(dataset_page):
    first = wait_and_capture(dataset_page, "TC_DS_05", By.XPATH, Locators.DATASET_CARD)
    first.click()
    link = wait_and_capture(dataset_page, "TC_DS_05", By.XPATH, Locators.DATASET_VIEW_DETAILS_LINK)
    assert link.is_displayed()
'''
# ─── SECTORS TAB TESTS ─────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def sectors_page(driver):
    load_homepage(driver)
    tab = wait_and_capture(
        driver, "SETUP_SEC_TAB", *Locators.SECTORS_TAB,
        condition=EC.element_to_be_clickable
    )
    tab.click()
    return driver

@pytest.mark.smoke
def test_TC_SEC_01_header_text(sectors_page):
    hdr = wait_and_capture(sectors_page, "TC_SEC_01", *Locators.SECTOR_HEADER)
    assert hdr.is_displayed()

@pytest.mark.smoke
def test_TC_SEC_02_search_bar(sectors_page):
    bar = wait_and_capture(sectors_page, "TC_SEC_02", *Locators.SECTOR_SEARCH_BAR)
    assert bar.is_displayed()

@pytest.mark.smoke
def test_TC_SEC_03_sort_dropdown(sectors_page):
    dd = wait_and_capture(sectors_page, "TC_SEC_03", *Locators.SECTOR_SORT_DROPDOWN)
    assert dd.is_displayed()

@pytest.mark.smoke
def test_TC_SEC_04_sector_cards(sectors_page):
    """TC_SEC_04: Sector cards are rendered on the Sectors tab"""
    # wait up to 10s for *all* cards to be present in the DOM
    cards = WebDriverWait(sectors_page, 10).until(
        EC.presence_of_all_elements_located(Locators.SECTOR_CARD)
    )

    count = len(cards)
    assert count > 0, (
        f"TC_SEC_04 failed: expected >0 sector cards, but found {count}. "
        "Check your `Locators.SECTOR_CARD` XPath."
    )

# @pytest.mark.parametrize("tc_id", ["TC_SEC_05", "TC_SEC_06", "TC_SEC_07"])
# def test_mobile_sectors(tc_id, sectors_page):
#     """Mobile checks for Sectors tab: cards, sort dropdown, and search bar"""
#     # simulate a phone viewport
#     sectors_page.set_window_size(375, 812)
#
#     if tc_id == "TC_SEC_05":
#         # wait for *all* sector cards to be present
#         cards = WebDriverWait(sectors_page, 10).until(
#             EC.presence_of_all_elements_located((By.XPATH, Locators.SECTOR_CARD))
#         )
#         count = len(cards)
#         assert count > 0, (
#             f"{tc_id} failed: expected >0 sector cards on mobile, but found {count}. "
#             "Verify `Locators.SECTOR_CARD`."
#         )
#
#     elif tc_id == "TC_SEC_06":
#         # wait for the sort dropdown to appear
#         dd = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, Locators.SECTOR_SORT_DROPDOWN_MOBILE))
#         )
#         assert dd.click(), (
#             f"{tc_id} failed: sort dropdown not visible on mobile. "
#             "Verify `Locators.SECTOR_SORT_DROPDOWN_MOBILE`."
#         )
#
#     else:  # TC_SEC_07
#         # wait for the search bar to appear
#         bar = wait_and_capture(sectors_page, "TC_SEC_02", By.XPATH, Locators.SECTOR_SEARCH_BAR)
#         assert bar.is_displayed(), (
#             f"{tc_id} failed: search bar not visible on mobile. "
#             "Verify `Locators.SECTOR_SEARCH_BAR`."
#         )

# ─── USE CASES TAB TESTS ───────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def usecases_page(driver):
    load_homepage(driver)
    tab = wait_and_capture(
        driver, "SETUP_UC_TAB", *Locators.USE_CASES_TAB,
        condition=EC.element_to_be_clickable
    )
    tab.click()
    return driver

@pytest.mark.smoke
def test_TC_UC_01_header_text(usecases_page):
    hdr = wait_and_capture(usecases_page, "TC_UC_01", *Locators.USE_CASES_HEADER)
    assert hdr.is_displayed()

@pytest.mark.smoke
def test_TC_UC_02_usecase_cards(usecases_page):
    """TC_UC_02: UseCase cards are rendered on the UseCase tab"""
    # wait up to 10s for *all* cards to be present in the DOM
    cards = WebDriverWait(usecases_page, 10).until(
        EC.presence_of_all_elements_located(Locators.USE_CASE_CARD)
    )

    count = len(cards)
    assert count > 0, (
        f"TC_UC_02 failed: expected >0 UseCase cards, but found {count}. "
        "Check your `Locators.USE_CASE_CARD` XPath."
    )
    
# 
# @pytest.mark.parametrize("tc_id", ["TC_UC_03","TC_UC_04"])
# def test_mobile_usecases(tc_id, usecases_page):
#     usecases_page.set_window_size(375, 812)
#     if tc_id == "TC_UC_03":
#         cards = wait_and_capture(
#             usecases_page, tc_id, By.XPATH, Locators.USE_CASE_CARD,
#             condition=lambda d: d.find_elements(By.XPATH, Locators.USE_CASE_CARD)
#         )
#         assert len(cards) > 0
#     else:
#         img = wait_and_capture(usecases_page, tc_id, By.XPATH, Locators.USE_CASE_CARD + "//img")
#         assert img.get_attribute("naturalWidth") != "0"

# ─── ABOUT TAB TESTS ──────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def about_page(driver):
    load_homepage(driver)
    tab = wait_and_capture(
        driver, "SETUP_ABOUT_TAB", *Locators.ABOUT_TAB,
        condition=EC.element_to_be_clickable
    )
    try:
        tab.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", tab)
    return driver

@pytest.mark.smoke
def test_TC_ABOUT_01_heading(about_page):
    h = wait_and_capture(about_page, "TC_ABOUT_01", *Locators.ABOUT_HEADING)
    assert h.is_displayed()

@pytest.mark.smoke
def test_TC_ABOUT_02_paragraph(about_page):
    p = wait_and_capture(about_page, "TC_ABOUT_02", *Locators.ABOUT_PARAGRAPH)
    assert p.is_displayed()

@pytest.mark.smoke
def test_TC_ABOUT_03_mobile_layout(about_page):
    about_page.set_window_size(375, 812)
    try:
        h = wait_and_capture(about_page, "TC_ABOUT_03", *Locators.ABOUT_HEADING)
        p = wait_and_capture(about_page, "TC_ABOUT_03", *Locators.ABOUT_PARAGRAPH)
        assert h.is_displayed() and p.is_displayed()
    finally:
        about_page.set_window_size(1920, 1080)

# # ─── LOGIN / SIGN UP TESTS ─────────────────────────────────────────────────────
# 
# @pytest.fixture(scope="function")
# def login_flow(driver):
#     load_homepage(driver)
#     link = wait_and_capture(
#         driver, "SETUP_LOGIN", By.XPATH, Locators.LOGIN_SIGNUP_LINK,
#         condition=EC.element_to_be_clickable
#     )
#     link.click()
#     return driver
# 
# def test_TC_LOGIN_01_form_loads(login_flow):
#     u = wait_and_capture(login_flow, "TC_LOGIN_01", By.XPATH, Locators.LOGIN_USERNAME_FIELD)
#     p = wait_and_capture(login_flow, "TC_LOGIN_01", By.XPATH, Locators.LOGIN_PASSWORD_FIELD)
#     assert u.is_displayed() and p.is_displayed()
# 
# def test_TC_LOGIN_02_mobile_layout(login_flow):
#     login_flow.set_window_size(375, 812)
#     u = wait_and_capture(login_flow, "TC_LOGIN_02", By.XPATH, Locators.LOGIN_USERNAME_FIELD)
#     p = wait_and_capture(login_flow, "TC_LOGIN_02", By.XPATH, Locators.LOGIN_PASSWORD_FIELD)
#     assert u.is_displayed() and p.is_displayed()
# 
# def test_TC_LOGIN_03_keyboard_triggers(login_flow):
#     login_flow.set_window_size(375, 812)
#     pwd = wait_and_capture(login_flow, "TC_LOGIN_03", By.XPATH, Locators.LOGIN_PASSWORD_FIELD)
#     pwd.click()
#     active = login_flow.switch_to.active_element
#     assert active == pwd