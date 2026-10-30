# tests/provider/smoke/test_prv_013_ind_ai_model_domain_dropdown.py

import pytest

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.ai_models_list_page import AiModelsListPage
from pages.provider.create_ai_model_page import CreateAiModelPage


# Below this, the dropdown is effectively empty (placeholder only) rather than
# genuinely short. Real count as of writing is 14 PromptDomain values; this
# threshold tolerates future additions/removals without needing an update.
MIN_REAL_DOMAIN_OPTIONS = 10


@pytest.mark.smoke
def test_prv_013_ind_ai_model_domain_dropdown(driver, base_url, test_credentials):
    """
    Test Case ID: test_prv_013_ind_ai_model_domain_dropdown
    Regression guard for DataSpaceFrontend#465/#463: the AI model edit
    details page's Domain dropdown is built from a static `enumValues()`
    helper reading the PromptDomain enum from codegen, replacing four
    runtime `__type` introspection queries that could be aborted by the
    browser under load and leave the dropdown permanently empty (cached by
    `staleTime: Infinity`). This never had coverage: the create-AI-model
    flow (test_prv_012) never touches the Domain field.
    Steps:
      1. Access Homepage and log in
      2. Navigate to My Dashboard -> AI Models -> Create AI Model
         (creation opens the Versions step), then open Model Information
      3. Read the options the empty Domain combobox lists
      4. Assert it populated with real PromptDomain values, not empty
    """
    driver.delete_all_cookies()

    home = HomePage(driver, base_url)
    email, password = test_credentials
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load"
    except Exception:
        pass

    # Step 1: Login
    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), (
        "test_prv_013: go_to_login(flow='provider') did not return ProviderHomePage"
    )

    # Step 2: My Dashboard -> AI Models -> Create AI Model
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        "test_prv_013: goto_my_dashboard() did not return MyDashboardPage"
    )

    ai_models_page = my_dash.click_ai_models_card()
    assert isinstance(ai_models_page, AiModelsListPage), (
        "test_prv_013: click_ai_models_card() did not return AiModelsListPage"
    )

    create_page = ai_models_page.click_add_new_ai_model()
    assert isinstance(create_page, CreateAiModelPage), (
        "test_prv_013: click_add_new_ai_model() did not return CreateAiModelPage"
    )

    create_page.go_to_details()

    # Step 3-4: Domain must list real PromptDomain options, not none.
    domain_values = create_page.get_domain_option_values()
    assert len(domain_values) >= MIN_REAL_DOMAIN_OPTIONS, (
        f"Step 3-4: Domain dropdown has only {len(domain_values)} real option(s) "
        f"(need >= {MIN_REAL_DOMAIN_OPTIONS}): {domain_values}. "
        "An empty/near-empty dropdown here is the #463 regression: enum values "
        "failed to load and the field is stuck unusable."
    )
