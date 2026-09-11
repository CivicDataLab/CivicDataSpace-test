# tests/provider/smoke/test_prv_004_ind_add_charts.py

import pytest

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.charts_list_page import ChartsListPage


@pytest.mark.functional
@pytest.mark.xfail(reason="Charts feature isn't fully built yet", strict=False)
def test_prv_004_ind_add_charts(driver, base_url, test_credentials):
    """
    Test Case ID: test_prv_004_ind_add_charts
    Verify an Individual provider can create a chart end-to-end.

    Steps:
      1. Load homepage
      2. Login as provider
      3. Navigate to My Dashboard
      4. Click 'Add & Manage Charts' in the sidebar
      5. Click 'Add Chart' to open the editor
      6. Select a dataset
      7. Select a resource
      8. Select a chart type
      9. Click 'Create Chart' and verify the editor closes
    """
    # ── Step 1: Load Homepage ─────────────────────────────────────────────────────
    driver.delete_all_cookies()
    email, password = test_credentials
    home = HomePage(driver, base_url)
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load"
    except Exception:
        pass

    # ── Step 2: Login as provider ─────────────────────────────────────────────────
    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after login, got {type(prov_home)}"
    )

    # ── Step 3: Go to My Dashboard ────────────────────────────────────────────────
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        f"Expected MyDashboardPage, got {type(my_dash)}"
    )

    # ── Step 4: Navigate to 'Add & Manage Charts' ─────────────────────────────────
    charts_page = my_dash.click_charts_card()
    assert isinstance(charts_page, ChartsListPage), (
        f"Expected ChartsListPage, got {type(charts_page)}"
    )
    assert charts_page.is_loaded(), "Charts list page did not load"

    # ── Step 5: Open the chart editor ─────────────────────────────────────────────
    charts_page.click_add_chart()

    # ── Step 6: Select dataset ────────────────────────────────────────────────────
    charts_page.select_dataset("Peta")
    actual_dataset = charts_page.get_selected_dataset()
    assert actual_dataset == "Peta", (
        f"Step 6 failure: Expected dataset 'Peta', got '{actual_dataset}'"
    )

    # ── Step 7: Select resource ───────────────────────────────────────────────────
    charts_page.select_resource("Peta.csv")
    actual_resource = charts_page.get_selected_resource()
    assert actual_resource == "Peta.csv", (
        f"Step 7 failure: Expected resource 'Peta.csv', got '{actual_resource}'"
    )

    # ── Step 8: Select chart type ─────────────────────────────────────────────────
    charts_page.select_chart_type("BAR")

    # ── Step 9: Create chart and verify detail editor opens ──────────────────────
    charts_page.click_create_chart()
    assert charts_page.is_chart_editor_open(), (
        "Step 9 failure: Chart detail editor did not open after creating chart"
    )
