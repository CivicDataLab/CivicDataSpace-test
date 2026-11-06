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

@pytest.mark.functional
@pytest.mark.smoke
@pytest.mark.timeout(360)
def test_prv_011_org_create_collaborative(driver, sample_logo_path, sample_cover_image_path, base_url, test_credentials, writable_org, sector_name):
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
    select_org = org_dash.select_org(writable_org)
    assert isinstance(select_org, OrganizationsPage), (
        "Step 4 failure: expected select_org() to return OrganizationsPage"
    )

    # ─── Step 5: Navigate to Collaboratives tab from side panel ─────────────────────────────
    collaboratives_page = org_dash.click_collaboratives_card()
    assert collaboratives_page.is_loaded(), "Step 5 failure: Collaboratives page did not load properly"

    # ─── Step 6: Click "Add New Collaborative" ─────────────────────────────────────────────
    create_collab = collaboratives_page.click_add_new_collaborative()
    assert isinstance(create_collab, CreateCollaborativePage)

    # About: cover, name, description, link, classification
    create_collab.upload_cover_image(sample_cover_image_path)
    assert create_collab.is_cover_image_uploaded(), "Cover image upload did not succeed."
    name = CollaborativeTestData.get_collaborative_name("organization")
    create_collab.enter_title(name)
    assert create_collab.get_title_value() == name
    summary = CollaborativeTestData.get_summary()
    create_collab.enter_summary(summary)
    assert create_collab.get_summary_value() == summary
    url = CollaborativeTestData.get_platform_url("organization")
    create_collab.enter_platform_url(url)
    assert create_collab.get_platform_url_value() == url
    create_collab.select_sectors([sector_name])
    assert sector_name in create_collab.get_selected_sectors()
    create_collab.select_sdg_goals(CollaborativeTestData.SDG_GOALS)
    assert CollaborativeTestData.SDG_GOALS in create_collab.get_selected_sdg_goals()
    create_collab.select_tags(CollaborativeTestData.TAGS)
    assert CollaborativeTestData.TAGS[0] in create_collab.get_selected_tags()
    create_collab.select_geography(CollaborativeTestData.GEOGRAPHY)
    assert CollaborativeTestData.GEOGRAPHY in create_collab.get_selected_geography()
    create_collab.click_continue()

    # People is optional
    create_collab.click_continue()

    # Content: connect a dataset and a use case
    assert create_collab.connect_first_dataset(), "No dataset could be connected."
    assert create_collab.connect_first_usecase(), "No use case could be connected."
    create_collab.click_continue()

    # Review & Publish
    detail = create_collab.click_publish()
    assert detail.is_published(), "Collaborative was not published."
