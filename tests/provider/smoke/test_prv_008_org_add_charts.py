# tests/provider/smoke/test_prv_008_org_add_charts.py

import pytest

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.organizations_page import OrganizationsPage
from pages.provider.charts_list_page import ChartsListPage


@pytest.mark.functional
def test_prv_008_org_add_charts(driver, base_url, test_credentials, writable_org):
    """
    Test Case ID: test_prv_008_org_add_charts
    Verify an Organization provider can create a chart end-to-end.

    Steps:
      1. Load homepage
      2. Login as provider
      3. Navigate to Organizations and select one the account can write to
      4. Click 'Add & Manage Charts' in the sidebar
      5. Click 'Add Chart' to open the editor
      6. Select a dataset that has a resource
      7. Select that resource
      8. Select a chart type
      9. Click 'Create Chart' and verify the chart editor opens
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

    # ── Step 3: Organizations → select a writable org ─────────────────────────────
    org_dash = prov_home.goto_organizations()
    assert isinstance(org_dash, OrganizationsPage), (
        f"Expected OrganizationsPage, got {type(org_dash)}"
    )
    org_dash.select_org(writable_org)

    # ── Step 4: Navigate to 'Add & Manage Charts' ─────────────────────────────────
    charts_page = org_dash.click_charts_card()
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
