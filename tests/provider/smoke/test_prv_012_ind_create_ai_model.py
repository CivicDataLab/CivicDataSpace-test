# tests/provider/smoke/test_prv_012_ind_create_ai_model.py

import pytest
from datetime import datetime

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.ai_models_list_page import AiModelsListPage
from pages.provider.create_ai_model_page import CreateAiModelPage


@pytest.mark.functional
def test_prv_012_ind_create_ai_model(driver, base_url, test_credentials):
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
    create_page.go_to_metadata_tab()

    # New models are created with isPublic=False; ensure Open Access is set
    # before any field save fires, otherwise handleSave() returns early.
    create_page.ensure_open_access()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_description = f"Automated AI model test {timestamp}"

    # (5a) Description
    create_page.enter_description(test_description)
    actual_desc = create_page.get_description_text()
    assert test_description in actual_desc, (
        f"Step 5a: Expected description to contain '{test_description}', got '{actual_desc}'"
    )

    # (5b) Target Users
    create_page.enter_target_users("Researchers and data scientists")

    # (5c) Intended Use
    create_page.enter_intended_use("Text generation for automated data analysis")

    # (5d) Sectors
    create_page.select_sectors(["Budgets"])

    # (5e) Tags
    create_page.select_tags(["Finance"])

    # (5f) Maximum Tokens
    create_page.select_max_tokens("4096")

    # (5g) Languages
    create_page.select_languages(["English"])

    # (5h) Model Website
    create_page.enter_model_website("https://example.com")

    # (5i) Geography
    create_page.select_geography("India")

    # Wait for autosave before navigating away
    create_page.wait_for_autosave()

    # ── Step 6: Create a version ──────────────────────────────────────────────
    create_page.go_to_version_tab()
    create_page.create_version(version_name="1.0")

    # ── Step 7: Add an access method ─────────────────────────────────────────
    create_page.add_access_method(endpoint_url="https://api.example.com/v1/completions")

    # ── Step 8: Publish ───────────────────────────────────────────────────────
    create_page.go_to_publish_tab()

    assert create_page.is_publish_button_enabled(), (
        "Step 8: Publish button is still disabled after filling all required fields"
    )

    create_page.click_publish()

    # ── Step 9: Assert published ──────────────────────────────────────────────
    assert create_page.is_published(), (
        "Step 9: AI model was not marked as published after clicking Publish"
    )
