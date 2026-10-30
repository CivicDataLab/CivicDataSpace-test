# tests/provider/functional/test_prv_007_org_create_usecase.py

import os

import pytest

from datetime import datetime
from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.create_usecase_page import CreateUsecasePage
from tests.data.test_data import UseCaseTestData
from pages.provider.organizations_page import OrganizationsPage

@pytest.mark.functional
@pytest.mark.smoke
# Previously failed reproducibly under concurrent (-n 3) provider-smoke CI runs
# (AssertionError: Summary mismatch, Found: '' - a race on the same worker that
# also failed test_prv_006, in the same run). Root cause: addUseCase's
# auto-generated title has 1-second resolution and both title and slug are
# globally unique, so two use cases created in the same second by any
# concurrent worker collided - the mutation raised instead of returning a
# usable record, leaving the newly-navigated-to usecase edit page in a broken
# state, so the summary field this test types into read back empty. Not a
# render/timing issue in the Quill editor - a genuine backend write race,
# independent of the org-collision theory ruled out earlier. Fixed in
# DataSpaceBackend PR #203 (retry-with-disambiguated-title/slug on collision),
# merged and deployed to dev 2026-09-18. Re-added smoke after confirming green
# under real -n 3 concurrent load against dev (0 reruns needed, vs failing
# every attempt pre-fix).
def test_prv_007_org_create_usecase(driver, sample_logo_path, base_url, test_credentials, writable_org, sector_name, cleanup):
    """
    Test Case ID: test_prv_007_org_create_usecase
    Verify User is able to create a UseCase end-to-end as an Organization provider.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and auto-login as provider
      3. Navigate to "Organizations"
      4. Select an organization
      5. Under UseCases section click "Create Use Case"
      6. Builder: set title and subtitle, upload a thumbnail, add a text block.
      7. Connect: tags, SDG goal, sector and geography; connect the first published dataset.
      8. Review & Publish: click "Publish Use Case".
      9. Assert the use case is listed as Published.
    """
    # ─── Step 1: Load Homepage ──────────────────────────────────────────────────────
    # Delete whatever this test creates, even when it fails part-way.
    cleanup.watch("usecase", writable_org)
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
        "test_prv_007: expected select_org() to return OrganizationsPage"
    )

    # ─── Step 5: Navigate to UseCases tab from side panel ─────────────────────────────
    usecases_page = org_dash.click_usecases_card()
    assert usecases_page.is_loaded(), "UseCases page did not load properly"

    # ─── Step 6: Click "Create Use Case" ─────────────────────────────────────────────
    create_uc = usecases_page.click_add_new_usecase()
    assert isinstance(create_uc, CreateUsecasePage), (
        f"Expected CreateUsecasePage after click, got {type(create_uc)}"
    )

    # ─── Step 7: Builder -- title, subtitle, thumbnail, a text block ────────────
    title = f"Org UC {datetime.now():%d%b%y_%H%M%S}"
    create_uc.enter_title(title)
    assert create_uc.get_title_value() == title

    subtitle = UseCaseTestData.get_summary("organization")
    create_uc.enter_subtitle(subtitle)
    assert create_uc.get_subtitle_value() == subtitle

    assert os.path.exists(sample_logo_path)
    create_uc.upload_thumbnail(sample_logo_path)

    body = "Automated test content block."
    create_uc.add_text_block(body)
    assert create_uc.get_text_block_value() == body

    # ─── Step 8: Connect -- classification and one published dataset ─────────
    create_uc.click_continue("connect")

    create_uc.select_tags(UseCaseTestData.TAGS)
    for tag in UseCaseTestData.TAGS:
        assert tag in create_uc.get_selected_tags()

    create_uc.select_sdg_goals(UseCaseTestData.SDG_GOALS)
    assert UseCaseTestData.SDG_GOALS in create_uc.get_selected_sdg_goals()

    create_uc.select_sectors([sector_name])
    assert sector_name in create_uc.get_selected_sectors()

    create_uc.select_geography(UseCaseTestData.GEOGRAPHY)
    geos = create_uc.get_selected_geography()
    assert any(g.startswith(UseCaseTestData.GEOGRAPHY) for g in geos), f"Geography chips: {geos}"

    assert create_uc.connect_first_dataset()

    # ─── Step 9: Review & Publish ───────────────────────────────────────────────
    create_uc.click_continue("publish")
    create_uc.click_publish(title)
    assert create_uc.is_published(), f"Use case {title!r} is not listed as Published after publishing"
