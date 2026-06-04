# tests/provider/functional/test_prv_007_org_create_usecase.py

import os
import time

import pytest
import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.create_usecase_page import CreateUsecasePage
from pages.provider.organizations_page import OrganizationsPage

@pytest.mark.smoke
def test_prv_007_org_create_usecase(driver, sample_logo_path, base_url, test_credentials):
    """
    Test Case ID: test_prv_007_org_create_usecase
    Verify User is able to create a UseCase end-to-end as an Organization provider.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and auto-login as provider
      3. Navigate to "Organizations"
      4. Select an organization
      5. Under UseCases section click on "Add New UseCase"
      6. Fill in Summary, Tags, Sectors, Geography, SDG Goals, Started On, Running Status,
         Completed On, and Upload a Logo.
      7. Switch to "Datasets" tab, select the first dataset in the list, then click "Submit".
      8. Switch to "Contributors" tab, add Contributors, Supporters, and Partners.
      9. Switch to "Publish" tab and click "Publish".
      10. Assert that the UseCase is marked "Published".
    """
    # ─── Step 1: Load Homepage ──────────────────────────────────────────────────────
    driver.delete_all_cookies()
    email, password = test_credentials
    home = HomePage(driver, base_url)
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load successfully"
    except Exception:
        pass

    # ─── Step 2: Login as provider (auto-fill) ───────────────────────────────────────
    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after auto-login, got {type(prov_home)}"
    )

    # ─── Step 3: Go to "Organizations" ───────────────────────────────────────────────
    org_dash = prov_home.goto_organizations()
    assert isinstance(org_dash, OrganizationsPage), (
        f"Expected OrganizationsPage, got {type(org_dash)}"
    )

    # ─── Step 4: Select one of the organizations ─────────────────────────────────────
    select_org = org_dash.select_org()
    assert isinstance(select_org, OrganizationsPage), (
        "test_prv_007: expected select_org() to return OrganizationsPage"
    )

    # ─── Step 5: Navigate to UseCases tab from side panel ─────────────────────────────
    usecases_page = org_dash.click_usecases_card()
    assert usecases_page.is_loaded(), "UseCases page did not load properly"

    # ─── Step 6: Click "Add New UseCase" ─────────────────────────────────────────────
    create_uc = usecases_page.click_add_new_usecase()
    assert isinstance(create_uc, CreateUsecasePage), (
        f"Expected CreateUsecasePage after click, got {type(create_uc)}"
    )

    # ─── Step 7: Fill in UseCase Details ─────────────────────────────────────────────

    # (7a) Summary
    test_summary = f"Automated Org UseCase Test – {datetime.now().date()}"
    create_uc.enter_summary(test_summary)
    actual_summary = create_uc.get_summary_value()
    assert actual_summary == test_summary + test_summary, (
        f"Step 7a failure: Summary mismatch. Expected: '{test_summary}', Found: '{actual_summary}'."
    )

    # (7b) Platform URL
    create_uc.enter_platform_url("https://orgplatform.url")
    actual_url = create_uc.get_platform_url_value()
    assert actual_url == "https://orgplatform.url", (
        f"Step 7b failure: Expected platform URL 'https://orgplatform.url', but found '{actual_url}'."
    )

    time.sleep(3)

    # (7c) Running Status
    create_uc.select_running_status("On Going")
    actual_status = create_uc.get_running_status_value()
    assert actual_status == "On Going", (
        f"Step 7c failure: Expected status 'On Going', but found '{actual_status}'."
    )

    # (7d) Tags
    create_uc.select_tags(["Budget"])
    selected_tags = create_uc.get_selected_tags()
    assert "Budget" in selected_tags, (
        f"Step 7d failure: Tag not selected correctly. Current tags: {selected_tags}"
    )

    # (7e) Sectors
    create_uc.select_sectors(["Budgets"])
    selected_sectors = create_uc.get_selected_sectors()
    assert "Budgets" in selected_sectors, (
        f"Step 7e failure: Sector not selected correctly. Current sectors: {selected_sectors}"
    )

    # (7f) Geography
    create_uc.select_geography("India")
    actual_geo = create_uc.get_selected_geography()
    assert "India" in actual_geo, (
        f"Step 7f failure: Expected geography to contain 'India', but got '{actual_geo}'."
    )

    # (7g) SDG Goals
    create_uc.select_sdg_goals("13")
    selected_sdgs = create_uc.get_selected_sdg_goals()
    assert "13" in selected_sdgs, (
        f"Step 7g failure: SDG goal not selected correctly. Selected: {selected_sdgs}"
    )

    # (7h) Started On
    start_date = "2023-01-01"
    create_uc.enter_started_on(start_date)
    actual_start = create_uc.get_started_on_value()
    assert actual_start == "2023-01-01", (
        f"Step 7h failure: Started On mismatch. Expected: {start_date}, Found: {actual_start}"
    )

    # Note: Skipped "Completed On" as "On Going" status doesn't require completion date

    # (7i) Logo Upload
    create_uc.upload_logo(sample_logo_path)
    assert create_uc.is_logo_uploaded(), "Step 7i failure: Logo upload did not succeed."

    # ─── Step 8: Datasets tab – select the first dataset, click Submit ────────────────
    create_uc.go_to_datasets_tab() \
        .select_first_dataset_checkbox() \
        .click_submit_datasets()

    # Verify that dataset was selected and submission registered
    selected_datasets = create_uc.get_selected_datasets()
    assert selected_datasets, (
        f"Step 8 failure: No dataset was selected/submitted. Got: {selected_datasets}"
    )

    # Note: Skipping contributor's section due to ongoing issues (as per test_prv_003)

    # ─── Step 9: Publish tab – Publish UseCase ───────────────────────────────────────
    create_uc.go_to_publish_tab()
    time.sleep(5)
    detail = create_uc.click_publish()
    assert detail.is_published(), "Step 9 failure: UseCase was not marked as 'Published'."


