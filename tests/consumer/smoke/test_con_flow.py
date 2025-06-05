# tests/consumer/smoke/test_con_flow.py

import pytest
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pages.home_page import HomePage


logger = logging.getLogger(__name__)

def test_con_001_access_platform(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    assert home.is_icon_visible(), "Con_001: Homepage icon not visible"

def test_con_002_access_all_data_page(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    print("DEBUG: after load(), driver.current_url =", driver.current_url)
    ds_page = home.go_to_all_data_page()
    ds_cards = ds_page.list_cards()
    assert ds_page.is_loaded(), "Con_002: Datasets page failed to load"
    assert len(ds_cards) > 0 , "Con_002: Datasets cards failed to load"


def test_con_003_verify_dataset_download(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    ds = home.go_to_all_data_page()
    assert ds.is_loaded()
    status, href = ds.download_dataset()
    assert status == 200

def test_con_004_access_sectors_page(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    sec_page   = home.go_to_sectors()
    sec_cards = sec_page.has_cards()
    assert sec_page.is_loaded(), "Con_004: Sectors page header missing"
    assert len(sec_cards) > 0, "Con_004: Sectors page Cards are missing"

def test_con_005_sector_cards_and_associated_datasets(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()

    # navigate to Sectors page
    sec_page = home.go_to_sectors()

    # download the first dataset of the first sector
    href, status = sec_page.download_first_associated_dataset(
        sector_index=0,
        dataset_index=0
    )

    # multi‐condition assert: both URL and status
    assert href.startswith("https://"), f"Invalid download URL: {href}"
    assert status == 200, f"Expected 200, got {status}"


def test_con_006_access_use_case_page(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    uc_page = home.go_to_usecases()
    uc_cards = uc_page.has_cards()
    assert uc_page.is_loaded(), "Con_006: Use Cases header missing"
    assert len(uc_cards) > 0, "Con_004: Sectors page Cards are missing"

def test_con_007_use_case_cards_and_associated_datasets(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    uc_page  = home.go_to_usecases()
    # download the first dataset of the first sector
    href, status = uc_page.download_first_associated_dataset(
        usecase_index=0,
        dataset_index=0
    )

    # multi‐condition assert: both URL and status
    assert href.startswith("https://"), f"Invalid download URL: {href}"
    assert status == 200, f"Expected 200, got {status}"

def test_con_008_access_publishers_page(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    pb_page = home.go_to_publishers()
    assert pb_page.is_loaded(), "Con_008: Publishers header missing"

@pytest.mark.parametrize("tc_id,view", [
    ("test_con_009", "all"),
    ("test_con_010", "org"),
    ("test_con_011", "ind"),
])
def test_publishers(tc_id, view, driver, base_url):

    # 1) navigate from home → publishers
    home = HomePage(driver, base_url)
    home.load()
    pub  = home.go_to_publishers()  # assumes HomepagePage has this

    # 2) list & assert cards exist
    cards = pub.list_publishers(view)
    assert cards, f"{tc_id} failed: no publisher cards in '{view}' view"

    # 3) click into first publisher
    detail = pub.open_publisher_by_index(0, view=view)

    # 4) list & assert use-cases under that publisher
    usecases = detail.list_usecases()
    assert usecases, f"{tc_id} failed: no use-case cards under publisher ({view})"

    # 5) click the first use-case and confirm URL
    detail.open_usecase_by_index(0)
    assert "/usecases/" in driver.current_url, (
        f"{tc_id} failed: did not navigate to use-case page, URL is {driver.current_url}"
    )

def test_con_012_access_about_us_page(driver, base_url):
    home = HomePage(driver, base_url)
    home.load()
    about_page = home.go_to_about()
    assert about_page.is_heading_visible(), "Con_010: About Us heading missing"
