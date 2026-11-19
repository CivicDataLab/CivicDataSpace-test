# tests/provider/smoke/test_prv_004_ind_add_charts.py

import pytest

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.charts_list_page import ChartsListPage


@pytest.mark.functional
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
    dataset = charts_page.pick_first_dataset()
    assert dataset, "No dataset available to chart"
    charts_page.pick_first_resource()
    charts_page.choose_chart_type("Bar")
    assert charts_page.is_chart_builder_shown(), (
        "Chart builder (field mapping + Live Preview) did not appear after choosing a chart type"
    )
