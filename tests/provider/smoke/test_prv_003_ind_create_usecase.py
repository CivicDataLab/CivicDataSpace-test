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

@pytest.mark.functional
def test_prv_003_ind_create_usecase(driver, sample_logo_path, base_url,test_credentials, sector_name):
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

    create_uc = usecases_page.click_add_new_usecase()
    assert isinstance(create_uc, CreateUsecasePage)

    # Builder: thumbnail, subtitle, one text block
    create_uc.upload_logo(sample_logo_path)
    assert create_uc.is_logo_uploaded(), "Thumbnail upload did not succeed."
    subtitle = f"Automated UseCase {datetime.now().strftime('%Y%m%d%H%M%S')}"
    create_uc.enter_subtitle(subtitle)
    assert create_uc.get_subtitle_value() == subtitle
    create_uc.add_text_content("Automated functional test content.")
    create_uc.click_continue()

    # Connect: taxonomy + dataset
    create_uc.select_tags(["Budget"])
    assert "Budget" in create_uc.get_selected_tags()
    create_uc.select_sectors([sector_name])
    assert sector_name in create_uc.get_selected_sectors()
    create_uc.select_geography("India")
    assert "India" in create_uc.get_selected_geography()
    create_uc.select_sdg_goals("13")
    assert "13" in create_uc.get_selected_sdg_goals()
    assert create_uc.select_first_dataset(), "No dataset could be linked."
    create_uc.click_continue()

    # Review & Publish
    create_uc.click_publish()
    assert create_uc.is_published(), "UseCase was not published."
