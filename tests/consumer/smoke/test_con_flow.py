# tests/consumer/smoke/test_con_flow.py
import logging
import pytest
import requests
from selenium.common.exceptions import TimeoutException
from pages.home_page import HomePage

logger = logging.getLogger(__name__)

# ---------- fixtures & helpers ----------
@pytest.fixture
def home(driver, base_url):
    """Loaded HomePage for each test."""
    page = HomePage(driver, base_url)
    page.load()
    return page

def _check_download(url: str, timeout: int = 10) -> int:
    """Return HTTP status for a HEAD request to *url*."""
    return requests.head(url, timeout=timeout, allow_redirects=True).status_code
# ----------------------------------------

@pytest.mark.smoke
def test_con_001_access_platform(home):
    assert home.is_icon_visible(), "Con_001: Homepage icon not visible"

@pytest.mark.smoke
def test_con_002_access_all_data_page(home):
    ds_page = home.go_to_all_data_page()
    assert ds_page.is_loaded(), "Con_002: Datasets page failed to load"
    assert ds_page.list_cards(), "Con_002: Dataset cards failed to load"

@pytest.mark.smoke
def test_con_003_verify_dataset_download(home):
    ds_page = home.go_to_all_data_page()
    assert ds_page.is_loaded(), "Con_003: Datasets page failed to load"
    href, _ = ds_page.download_dataset()
    assert _check_download(href) == 200, f"Con_003: Download failed – {href}"

@pytest.mark.smoke
def test_con_004_access_sectors_page(home):
    sec_page = home.go_to_sectors()
    assert sec_page.is_loaded(), "Con_004: Sectors page failed to load"
    assert sec_page.has_cards(), "Con_004: Sector cards missing"

@pytest.mark.smoke
@pytest.mark.parametrize("sector_index,dataset_index", [(0, 0)])
def test_con_005_sector_download(home, sector_index, dataset_index):
    sec_page = home.go_to_sectors()
    href, _ = sec_page.download_first_associated_dataset(
        sector_index, dataset_index
    )
    status = _check_download(href)
    assert href.startswith("https"), f"Con_005: Invalid URL {href}"
    assert status == 200, f"Con_005: Expected 200, got {status}"

@pytest.mark.smoke
def test_con_006_access_use_case_page(home):
    uc_page = home.go_to_usecases()
    assert uc_page.is_loaded(), "Con_006: Use-Cases page failed to load"
    assert uc_page.has_cards(), "Con_006: Use-Case cards missing"

@pytest.mark.smoke
@pytest.mark.parametrize("usecase_index,dataset_index", [(0, 0)])
def test_con_007_use_case_download(home, usecase_index, dataset_index):
    uc_page = home.go_to_usecases()
    href, _ = uc_page.download_first_associated_dataset(
        usecase_index, dataset_index
    )
    status = _check_download(href)
    assert href.startswith("https"), f"Con_007: Invalid URL {href}"
    assert status == 200, f"Con_007: Expected 200, got {status}"

@pytest.mark.smoke
def test_con_008_access_publishers_page(home):
    pb_page = home.go_to_publishers()
    assert pb_page.is_loaded(), "Con_008: Publishers page failed to load"

@pytest.mark.parametrize(
    "tc_id,view",
    [("test_con_009", "all"), ("test_con_010", "org"), ("test_con_011", "ind")],
)

@pytest.mark.timeout(60)
def test_publishers_flow(tc_id, view, home, driver):
    pub   = home.go_to_publishers()
    cards = pub.list_publishers(view)
    assert cards, f"{tc_id}: no publisher cards in '{view}' view"

    for idx in range(len(cards)):
        try:
            detail = pub.open_publisher_by_index(idx, view=view)
            usecases = detail.list_usecases()
            if usecases:
                break
        except TimeoutException:
            # Couldn’t open this publisher or its use-cases; try next one
            continue
    else:
        pytest.skip(f"{tc_id}: no publishers with use-cases in '{view}' view")

    # open the first use-case we found
    detail.open_usecase_by_index(0)
    assert "/usecases/" in driver.current_url, (
        f"{tc_id}: expected /usecases/ in URL, got {driver.current_url}"
    )

@pytest.mark.smoke
def test_con_012_access_about_us_page(home):
    about_page = home.go_to_about()
    assert about_page.is_heading_visible(), "Con_012: About Us heading missing"
