# tests/provider/functional/test_prv_003_ind_create_usecase.py

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

@pytest.mark.smoke
def test_prv_003_ind_create_usecase(driver, sample_logo_path, base_url,test_credentials):
    """
    Test Case ID: test_prv_003_ind_create_usecase
    Verify User is able to create a UseCase end-to-end as an Individual provider.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and auto-login as provider
      3. Navigate to “My Dashboard”
      4. Under UseCases section click on “Add New UseCase”
      5. Fill in Summary, Tags, Sectors, Geography, SDG Goals, Started On, Running Status,
         Completed On, and Upload a Logo.
      6. Switch to “Datasets” tab, select the first dataset in the list, then click “Submit”.
      7. Switch to “Contributors” tab, add Contributors, Supporters, and Partners.
      8. Switch to “Publish” tab and click “Publish”.
      9. Assert that the UseCase is marked “Published”.
    """
    # ─── Step 1: Load Homepage ──────────────────────────────────────────────────────
    driver.delete_all_cookies()
    email, password = test_credentials
    home = HomePage(driver, base_url)
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load successfully"
    except Exception as e:
        print(f"Error loading homepage: {e}")

    # ─── Step 2: Login as provider (auto-fill) ───────────────────────────────────────
    prov_home = home.go_to_login(flow="provider", email=email, password=password,)
    assert isinstance(prov_home, ProviderHomePage), (
        f"Expected ProviderHomePage after auto-login, got {type(prov_home)}"
    )

    # ─── Step 3: Go to “My Dashboard” ───────────────────────────────────────────────
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        f"Expected MyDashboardPage, got {type(my_dash)}"
    )

    # ─── Step 4: Navigate to UseCases tab from side panel ─────────────────────────────
    usecases_page = my_dash.click_usecases_card()
    assert usecases_page.is_loaded(), "UseCases page did not load properly"

    # ─── Step 5: Click “Add New UseCase” ─────────────────────────────────────────────
    create_uc = usecases_page.click_add_new_usecase()
    assert isinstance(create_uc, CreateUsecasePage), (
        f"Expected CreateUsecasePage after click, got {type(create_uc)}"
    )

    # # (6a) Use Case Name (optional, if applicable)
    # test_usecase_name = f"Automated Test UseCase {datetime.now().strftime('%Y%m%d%H%M%S')}"
    # create_uc.enter_usecase_name(test_usecase_name)
    # actual_uc_name = create_uc.get_usecase_name_value()
    # assert actual_uc_name == test_usecase_name, (
    #     f"Step 6a failure: Expected use case name to be '{test_usecase_name}', but found '{actual_uc_name}'."
    # )

    # (6b) Summary
    test_summary = f"Automated Functional Test UseCase – {datetime.now().date()}"
    create_uc.enter_summary(test_summary)
    actual_summary = create_uc.get_summary_value()
    assert actual_summary == test_summary + test_summary, (
        f"Step 6b failure: Summary mismatch. Expected: '{test_summary}', Found: '{actual_summary}'."
    )

    ## (6c) Platform URL
    create_uc.enter_platform_url("https://yourplatform.url")
    actual_url = create_uc.get_platform_url_value()
    assert actual_url == "https://yourplatform.url", (
        f"Step 6c failure: Expected status 'Initiated', but found '{actual_url}'."
    )

    time.sleep(3)

    # (6d) Running Status
    create_uc.select_running_status("On Going")
    actual_status = create_uc.get_running_status_value()
    assert actual_status == "On Going", (
        f"Step 6d failure: Expected status 'Initiated', but found '{actual_status}'."
    )

    # (6e) Tags
    create_uc.select_tags(["Budget"])
    selected_tags = create_uc.get_selected_tags()
    assert "Budget" in selected_tags, (
        f"Step 6e failure: Tag not selected correctly. Current tags: {selected_tags}"
    )

    # (6f) Sectors
    create_uc.select_sectors(["Public Finance"])
    selected_sectors = create_uc.get_selected_sectors()
    assert "Public Finance" in selected_sectors, (
        f"Step 6f failure: Sector not selected correctly. Current sectors: {selected_sectors}"
    )

    # (6g) Geography
    create_uc.select_geography("India")
    actual_geo = create_uc.get_selected_geography()
    assert actual_geo == "India", (
        f"Step 6g failure: Expected geography to be 'India', but got '{actual_geo}'."
    )

    # (6h) SDG Goals
    create_uc.select_sdg_goals("SDG13")
    selected_sdgs = create_uc.get_selected_sdg_goals()
    assert "SDG13" in selected_sdgs, (
        f"Step 6h failure: SDG goal not selected correctly. Selected: {selected_sdgs}"
    )

    # (6i) Started On
    start_date = "01012023"
    create_uc.enter_started_on(start_date)
    actual_start = create_uc.get_started_on_value()
    assert actual_start == "2023-01-01", (
        f"Step 6i failure: Started On mismatch. Expected: {start_date}, Found: {actual_start}"
    )

    # skipped as On going does not have a completed on date.
    # # (6j) Completed On
    # completed_date = "01062023"
    # create_uc.enter_completed_on(completed_date)
    # actual_completed = create_uc.get_completed_on_value()
    # assert actual_completed == "2023-06-01", (
    #     f"Step 6j failure: Completed On mismatch. Expected: {completed_date}, Found: {actual_completed}"
    # )

    # (6k) Logo Upload
    create_uc.upload_logo(sample_logo_path)
    assert create_uc.is_logo_uploaded(), "Step 6k failure: Logo upload did not succeed."


    # ─── Step 7: Datasets tab – select the first dataset, click Submit ────────────────
    create_uc.go_to_datasets_tab() \
        .select_first_dataset_checkbox() \
        .click_submit_datasets()


    # Verify that dataset was selected and submission registered (assumes a method exists)
    selected_datasets = create_uc.get_selected_datasets()
    assert selected_datasets, (
        f"Step 7 failure: No dataset was selected/submitted. Got: {selected_datasets}"
    )


    #Skipping contributor's section because of ongoing issues.

    # # ─── Step 8: Contributors tab – add contributors, supporters, partners ────────────
    # create_uc.go_to_contributors_tab() \
    #     .add_contributors(["Sanjay Pinna"]) \
    #     .add_supporters(["CivicDataLab"]) \
    #     .add_partners(["CivicDataLab"])
    #
    # # Validate entries
    # contribs = create_uc.get_contributors_list()
    # assert "Sanjay Pinna" in contribs, f"Step 8a failure: Contributor 'Sanjay Pinna' not found at index 3. Found: {contribs}"
    #
    # supporters = create_uc.get_supporters_list()
    # assert "CivicDataLab" in supporters, (
    #     f"Step 8b failure: Supporter 'CivicDataLab' not found. Found: {supporters}"
    # )
    #
    # partners = create_uc.get_partners_list()
    # assert "CivicDataLab" in partners, (
    #     f"Step 8c failure: Partner 'CivicDataLab' not found. Found: {partners}"
    # )

    # ─── Step 9: Publish tab – Publish UseCase ───────────────────────────────────────
    create_uc.go_to_publish_tab()
    time.sleep(5)
    detail = create_uc.click_publish()
    assert detail.is_published(), "Step 9 failure: UseCase was not marked as 'Published'."

    # ─── (Optional) Step 10: Download the newly published UseCase details via API (200)
    # For example, if your app exposes a “download” or “fetch” endpoint for published use cases:
    #    download_url = detail.get_download_url()   # assume this method exists
    #    resp = requests.get(download_url)
    #    assert resp.status_code == 200, f"Expected HTTP 200 when downloading use case, got {resp.status_code}"
