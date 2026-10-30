# tests/provider/functional/test_prv_003_ind_create_usecase.py

import os

import pytest

from datetime import datetime
from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.create_usecase_page import CreateUsecasePage
from tests.data.test_data import UseCaseTestData

@pytest.mark.functional
def test_prv_003_ind_create_usecase(driver, sample_logo_path, base_url,test_credentials, sector_name):
    """
    Test Case ID: test_prv_003_ind_create_usecase
    Verify User is able to create a UseCase end-to-end as an Individual provider.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and auto-login as provider
      3. Navigate to “My Dashboard”
      4. Under UseCases section click "Create Use Case"
      5. Builder: set title and subtitle, upload a thumbnail, add a text block.
      6. Connect: tags, SDG goal, sector and geography; connect the first published dataset.
      7. Review & Publish: click "Publish Use Case".
      8. Assert the use case is listed as Published.
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

    # ─── Step 5: Click "Create Use Case" ─────────────────────────────────────────────
    create_uc = usecases_page.click_add_new_usecase()
    assert isinstance(create_uc, CreateUsecasePage), (
        f"Expected CreateUsecasePage after click, got {type(create_uc)}"
    )

    # ─── Step 6: Builder -- title, subtitle, thumbnail, a text block ────────────
    title = f"Ind UC {datetime.now():%d%b%y_%H%M%S}"
    create_uc.enter_title(title)
    assert create_uc.get_title_value() == title

    subtitle = UseCaseTestData.get_summary("individual")
    create_uc.enter_subtitle(subtitle)
    assert create_uc.get_subtitle_value() == subtitle

    assert os.path.exists(sample_logo_path)
    create_uc.upload_thumbnail(sample_logo_path)

    body = "Automated test content block."
    create_uc.add_text_block(body)
    assert create_uc.get_text_block_value() == body

    # ─── Step 7: Connect -- classification and one published dataset ─────────
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

    # ─── Step 8: Review & Publish ───────────────────────────────────────────────
    create_uc.click_continue("publish")
    create_uc.click_publish(title)
    assert create_uc.is_published(), f"Use case {title!r} is not listed as Published after publishing"
