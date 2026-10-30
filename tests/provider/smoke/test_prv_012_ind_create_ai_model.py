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
      4. Click "Create AI Model" (opens the Versions step)
      5. Add Version 1.0 with a Custom API access method
      6. Continue to Model Information: name, description, domain, intended
         use, sectors, tags, languages, licence, website, geography
      7. Continue to Review & Publish, publish
      8. Assert the model is listed as Published
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

    # ── Step 5: Add a version with one access method ─────────────────────────
    create_page.add_version(
        name="1.0",
        access_name="Automation Custom API",
        model_id="automation-model",
        endpoint_url="https://api.example.com/v1/completions",
    )
    create_page.click_continue("details")

    # ── Step 6: Model Information ─────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    model_name = f"Ind AI Model {timestamp}"
    test_description = f"Automated AI model test {timestamp}"

    create_page.enter_model_name(model_name)
    assert create_page.get_model_name_value() == model_name, (
        f"Step 6: Model Name did not keep '{model_name}'"
    )

    create_page.enter_description(test_description)
    actual_desc = create_page.get_description_text()
    assert test_description in actual_desc, (
        f"Step 6: Expected description to contain '{test_description}', got '{actual_desc}'"
    )

    create_page.select_domain("Agriculture")
    create_page.enter_intended_use("Text generation for automated data analysis")
    create_page.select_sectors([sector_name])
    assert sector_name in create_page.get_selected_sectors(), (
        f"Step 6: Sector '{sector_name}' was not selected"
    )
    create_page.select_tags(["Finance"])
    create_page.select_languages(["English"])
    create_page.select_usage_license("Creative Commons BY 4.0")
    create_page.enter_model_website("https://example.com")
    create_page.select_geography("India")

    # ── Step 7: Publish ───────────────────────────────────────────────────────
    create_page.click_continue("publish")
    create_page.click_publish(model_name)

    # ── Step 8: Assert published ──────────────────────────────────────────────
    assert create_page.is_published(), (
        f"Step 8: '{model_name}' is not listed as Published after publishing"
    )
