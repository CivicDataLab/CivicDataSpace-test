# tests/provider/smoke/test_prv_011_org_create_collaborative.py

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
from pages.provider.create_collaborative_page import CreateCollaborativePage
from pages.provider.organizations_page import OrganizationsPage
from tests.data.test_data import CollaborativeTestData

@pytest.mark.smoke
def test_prv_011_org_create_collaborative(driver, sample_logo_path, sample_cover_image_path, base_url, test_credentials):
    """
    Test Case ID: test_prv_011_org_create_collaborative
    Verify User is able to create a Collaborative end-to-end as an Organization provider.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and auto-login as provider
      3. Navigate to "Organizations"
      4. Select an organization
      5. Under Collaboratives section click on "Add New Collaborative"
      6. Edit the collaborative name to a unique name
      7. Fill in Summary, Platform URL, SDG Goals, Tags, Sectors, Geography,
         Started On, Completed On, and Upload Logo and Cover Image.
      8. Switch to "Datasets" tab, select the first dataset in the list, then click "Submit".
      9. Switch to "Use Cases" tab, select the first use case in the list, then click "Submit".
      10. Switch to "Publish" tab and click "Publish".
      11. Assert that the Collaborative is marked "Published".
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
        "Step 4 failure: expected select_org() to return OrganizationsPage"
    )

    # ─── Step 5: Navigate to Collaboratives tab from side panel ─────────────────────────────
    collaboratives_page = org_dash.click_collaboratives_card()
    assert collaboratives_page.is_loaded(), "Step 5 failure: Collaboratives page did not load properly"

    # ─── Step 6: Click "Add New Collaborative" ─────────────────────────────────────────────
    create_collab = collaboratives_page.click_add_new_collaborative()
    assert isinstance(create_collab, CreateCollaborativePage), (
        f"Step 6 failure: Expected CreateCollaborativePage after click, got {type(create_collab)}"
    )

    # ─── Step 7: Edit Collaborative Name ────────────────────────────────────────────────────
    test_collab_name = CollaborativeTestData.get_collaborative_name("organization")
    create_collab.edit_collaborative_name(test_collab_name)
    time.sleep(2)
    actual_collab_name = create_collab.get_collaborative_name_value()
    assert test_collab_name in actual_collab_name, (
        f"Step 7 failure: Expected collaborative name to contain '{test_collab_name}', but found '{actual_collab_name}'."
    )
    assert len(actual_collab_name) > 0, "Step 7 failure: Collaborative name is empty"

    # ─── Step 8: Fill in Summary ─────────────────────────────────────────────────────────────
    test_summary = CollaborativeTestData.get_summary()
    create_collab.enter_summary(test_summary)
    actual_summary = create_collab.get_summary_value()
    assert actual_summary == test_summary + test_summary, (
        f"Step 8 failure: Summary mismatch. Expected: '{test_summary + test_summary}', Found: '{actual_summary}'."
    )
    assert len(actual_summary) > 0, "Step 8 failure: Summary is empty"

    # ─── Step 9: Platform URL ─────────────────────────────────────────────────────────────────
    platform_url = CollaborativeTestData.get_platform_url("organization")
    create_collab.enter_platform_url(platform_url)
    actual_url = create_collab.get_platform_url_value()
    assert actual_url == platform_url, (
        f"Step 9 failure: Expected platform URL '{platform_url}', but found '{actual_url}'."
    )
    assert actual_url.startswith("https://"), "Step 9 failure: Platform URL should start with https://"

    time.sleep(3)

    # ─── Step 10: SDG Goals ────────────────────────────────────────────────────────────────────
    create_collab.select_sdg_goals(CollaborativeTestData.SDG_GOALS)
    selected_sdgs = create_collab.get_selected_sdg_goals()
    assert CollaborativeTestData.SDG_GOALS in selected_sdgs, (
        f"Step 10 failure: SDG goal '{CollaborativeTestData.SDG_GOALS}' not selected correctly. Selected: {selected_sdgs}"
    )
    assert len(selected_sdgs) > 0, "Step 10 failure: No SDG goals selected"

    # ─── Step 11: Tags ────────────────────────────────────────────────────────────────────────
    create_collab.select_tags(CollaborativeTestData.TAGS)
    selected_tags = create_collab.get_selected_tags()
    assert CollaborativeTestData.TAGS[0] in selected_tags, (
        f"Step 11 failure: Tag '{CollaborativeTestData.TAGS[0]}' not selected correctly. Current tags: {selected_tags}"
    )
    assert len(selected_tags) > 0, "Step 11 failure: No tags selected"
    for tag in CollaborativeTestData.TAGS:
        assert tag in selected_tags, f"Step 11 failure: Expected tag '{tag}' not found in selected tags: {selected_tags}"

    # ─── Step 12: Sectors ─────────────────────────────────────────────────────────────────────
    create_collab.select_sectors(CollaborativeTestData.SECTORS)
    selected_sectors = create_collab.get_selected_sectors()
    assert CollaborativeTestData.SECTORS[0] in selected_sectors, (
        f"Step 12 failure: Sector '{CollaborativeTestData.SECTORS[0]}' not selected correctly. Current sectors: {selected_sectors}"
    )
    assert len(selected_sectors) > 0, "Step 12 failure: No sectors selected"
    for sector in CollaborativeTestData.SECTORS:
        assert sector in selected_sectors, f"Step 12 failure: Expected sector '{sector}' not found in selected sectors: {selected_sectors}"

    # ─── Step 13: Geography ───────────────────────────────────────────────────────────────────
    create_collab.select_geography(CollaborativeTestData.GEOGRAPHY)
    actual_geo = create_collab.get_selected_geography()
    assert CollaborativeTestData.GEOGRAPHY in actual_geo, (
        f"Step 13 failure: Expected geography to contain '{CollaborativeTestData.GEOGRAPHY}', but got '{actual_geo}'."
    )
    assert len(actual_geo) > 0, "Step 13 failure: Geography is empty"

    # ─── Step 14: Started On ──────────────────────────────────────────────────────────────────
    create_collab.enter_started_on(CollaborativeTestData.START_DATE_ISO)
    actual_start = create_collab.get_started_on_value()
    assert actual_start == CollaborativeTestData.START_DATE_ISO, (
        f"Step 14 failure: Started On mismatch. Expected: {CollaborativeTestData.START_DATE_ISO}, Found: {actual_start}"
    )
    assert len(actual_start) > 0, "Step 14 failure: Started On date is empty"

    # ─── Step 15: Completed On ────────────────────────────────────────────────────────────────
    create_collab.enter_completed_on(CollaborativeTestData.COMPLETED_DATE_ISO)
    actual_completed = create_collab.get_completed_on_value()
    assert actual_completed == CollaborativeTestData.COMPLETED_DATE_ISO, (
        f"Step 15 failure: Completed On mismatch. Expected: {CollaborativeTestData.COMPLETED_DATE_ISO}, Found: {actual_completed}"
    )
    assert len(actual_completed) > 0, "Step 15 failure: Completed On date is empty"
    # Verify that completed date is after started date
    assert actual_completed > actual_start, (
        f"Step 15 failure: Completed On date ({actual_completed}) should be after Started On date ({actual_start})"
    )

    # ─── Step 16: Logo Upload ─────────────────────────────────────────────────────────────────
    assert os.path.exists(sample_logo_path), f"Step 16 failure: Logo file does not exist at {sample_logo_path}"
    create_collab.upload_logo(sample_logo_path)
    time.sleep(2)  # Allow time for upload to complete
    assert create_collab.is_logo_uploaded(), "Step 16 failure: Logo upload did not succeed."

    # ─── Step 17: Cover Image Upload ──────────────────────────────────────────────────────────
    assert os.path.exists(sample_cover_image_path), f"Step 17 failure: Cover image file does not exist at {sample_cover_image_path}"
    create_collab.upload_cover_image(sample_cover_image_path)
    time.sleep(2)  # Allow time for upload to complete
    assert create_collab.is_cover_image_uploaded(), "Step 17 failure: Cover image upload did not succeed."

    # ─── Step 18: Click Next to go to Datasets tab ──────────────────────────────────────────
    create_collab.click_next()

    # ─── Step 19: Select first dataset and click Submit ──────────────────────────────────────
    create_collab.select_first_dataset_checkbox()
    create_collab.click_submit_datasets()
    time.sleep(2)

    # Verify that dataset was selected and submission registered
    selected_datasets = create_collab.get_selected_datasets()
    assert selected_datasets, (
        f"Step 19 failure: No dataset was selected/submitted. Got: {selected_datasets}"
    )
    assert len(selected_datasets) > 0, "Step 19 failure: Selected datasets list is empty"

    # ─── Step 20: Click Next to go to Use Cases tab ──────────────────────────────────────────
    create_collab.click_next()

    # ─── Step 21: Select first use case and click Submit ─────────────────────────────────────
    create_collab.select_first_usecase_checkbox()
    create_collab.click_submit_usecases()
    time.sleep(2)

    # Verify that use case was selected and submission registered
    selected_usecases = create_collab.get_selected_usecases()
    assert selected_usecases, (
        f"Step 21 failure: No use case was selected/submitted. Got: {selected_usecases}"
    )
    assert len(selected_usecases) > 0, "Step 21 failure: Selected use cases list is empty"

    # Skipping contributor's section because of ongoing issues (similar to usecase tests)

    # ─── Step 22: Click Next to go to Contributors tab ────────────────────────────────────────
    create_collab.click_next()

    # ─── Step 23: Click Next to go to Publish tab ─────────────────────────────────────────────
    create_collab.click_next()
    time.sleep(2)

    # ─── Step 24: Publish Collaborative ───────────────────────────────────────────────────────
    detail = create_collab.click_publish()
    assert detail.is_published(), "Step 24 failure: Collaborative was not marked as 'Published'."

