# tests/provider/smoke/test_prv_012_ind_create_ai_model.py

import pytest
from datetime import datetime

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.ai_models_list_page import AiModelsListPage
from pages.provider.create_ai_model_page import CreateAiModelPage


@pytest.mark.functional
@pytest.mark.smoke
def test_prv_012_ind_create_ai_model(driver, base_url, test_credentials, sector_name):
    """
    Test Case ID: test_prv_012_ind_create_ai_model
    Verify an Individual provider can create and publish an AI Model end-to-end.
    Steps:
      1. Access Homepage
      2. Log in as provider
      3. Navigate to My Dashboard → AI Models
      4. Click "Add New AI Model"
      5. Fill Metadata (description, target users, intended use, sectors,
         tags, max tokens, languages, model website, geography)
      6. Create a version (Version 1.0)
      7. Add an access method (Custom API endpoint)
      8. Publish the model
      9. Assert the model is published
    """
    driver.delete_all_cookies()
    email, password = test_credentials

    # ── Step 1-2: Load homepage and log in ────────────────────────────────────
    home = HomePage(driver, base_url)
    try:
        if not home.is_loaded():
            home.load()
    except Exception:
        pass

    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), (
        "test_prv_012: go_to_login(flow='provider') did not return ProviderHomePage"
    )

    # ── Step 3: Navigate to My Dashboard → AI Models ─────────────────────────
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        "test_prv_012: goto_my_dashboard() did not return MyDashboardPage"
    )

    ai_models_page = my_dash.click_ai_models_card()
    assert isinstance(ai_models_page, AiModelsListPage), (
        "test_prv_012: click_ai_models_card() did not return AiModelsListPage"
    )

    # ── Step 4: Open the AI model creation form ───────────────────────────────
    create_page = ai_models_page.click_add_new_ai_model()
    assert isinstance(create_page, CreateAiModelPage), (
        "test_prv_012: click_add_new_ai_model() did not return CreateAiModelPage"
    )

    # ── Step 5: Fill Metadata tab ─────────────────────────────────────────────
    # Versions: one version with a Custom API access method
    create_page.add_version_with_access("1.0", "https://api.example.com/v1/completions")
    create_page.click_continue()

    # Model Information: description, domain, sector, language support, license
    create_page.fill_model_information(
        f"Automated AI model test {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", sector_name)
    create_page.click_continue()

    # Review & Publish
    create_page.click_publish_model()
    assert create_page.is_model_published(), "AI model was not published."
