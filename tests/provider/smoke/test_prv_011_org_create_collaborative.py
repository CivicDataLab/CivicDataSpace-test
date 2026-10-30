# tests/provider/smoke/test_prv_011_org_create_collaborative.py

import os

import pytest

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.create_collaborative_page import CreateCollaborativePage
from pages.provider.organizations_page import OrganizationsPage
from tests.data.test_data import CollaborativeTestData

@pytest.mark.functional
@pytest.mark.smoke
@pytest.mark.timeout(360)
def test_prv_011_org_create_collaborative(driver, sample_logo_path, sample_cover_image_path, base_url, test_credentials, writable_org, sector_name, cleanup):
    """
    Test Case ID: test_prv_011_org_create_collaborative
    Verify User is able to create a Collaborative end-to-end as an Organization provider.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and auto-login as provider
      3. Navigate to "Organizations"
      4. Select an organization
      5. Under Collaboratives click "Create Collaborative"
      6. Edit the name, description, external link, sectors, SDG goal, tags,
         geography, cover image and logo (About step).
      7. Continue past People, then connect the first published dataset and use case (Content).
      8. Continue to Review & Publish and click "Publish Collaborative".
      9. Assert the collaborative is listed as Published.
    """
    # ─── Step 1: Load Homepage ──────────────────────────────────────────────────────
    # Delete whatever this test creates, even when it fails part-way.
    cleanup.watch("collaborative", writable_org)
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

    # ─── Step 6: Click "Create Collaborative" ─────────────────────────────────────────────
    create_collab = collaboratives_page.click_add_new_collaborative()
    assert isinstance(create_collab, CreateCollaborativePage), (
        f"Step 6 failure: Expected CreateCollaborativePage after click, got {type(create_collab)}"
    )

    # ─── Step 7: About -- name, description, link, classification, images ─────────
    test_collab_name = CollaborativeTestData.get_collaborative_name("organization")
    create_collab.edit_collaborative_name(test_collab_name)
    assert create_collab.get_collaborative_name_value() == test_collab_name, (
        f"Name did not stick: {create_collab.get_collaborative_name_value()!r}"
    )

    description = CollaborativeTestData.get_summary()
    create_collab.enter_description(description)
    assert create_collab.get_description_value() == description

    platform_url = CollaborativeTestData.get_platform_url("organization")
    create_collab.enter_platform_url(platform_url)
    assert create_collab.get_platform_url_value() == platform_url

    create_collab.select_sectors([sector_name])
    assert sector_name in create_collab.get_selected_sectors()

    create_collab.select_sdg_goals(CollaborativeTestData.SDG_GOALS)
    assert CollaborativeTestData.SDG_GOALS in create_collab.get_selected_sdg_goals()

    create_collab.select_tags(CollaborativeTestData.TAGS)
    selected_tags = create_collab.get_selected_tags()
    for tag in CollaborativeTestData.TAGS:
        assert tag in selected_tags, f"Tag {tag!r} missing from {selected_tags}"

    create_collab.select_geography(CollaborativeTestData.GEOGRAPHY)
    geos = create_collab.get_selected_geography()
    assert any(g.startswith(CollaborativeTestData.GEOGRAPHY) for g in geos), f"Geography chips: {geos}"

    assert os.path.exists(sample_cover_image_path)
    create_collab.upload_cover_image(sample_cover_image_path)
    assert os.path.exists(sample_logo_path)
    create_collab.upload_logo(sample_logo_path)

    # ─── Step 8: People is optional; Content connects a dataset and a use case ──────
    create_collab.click_continue("people")
    create_collab.click_continue("content")
    dataset_title = create_collab.connect_first_dataset()
    usecase_title = create_collab.connect_first_usecase()
    assert dataset_title and usecase_title

    # ─── Step 9: Review & Publish ───────────────────────────────────────────────────
    create_collab.click_continue("publish")
    create_collab.click_publish(test_collab_name)
    assert create_collab.is_published(), (
        f"Collaborative {test_collab_name!r} is not listed as Published after publishing"
    )
