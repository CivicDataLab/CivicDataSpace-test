# tests/provider/functional/test_prv_func_214_aimodel_max_tokens.py
#
# DataSpaceFrontend#558: a "Maximum Tokens" select on the AI model Model
# Information page, shown (formatted with a thousands separator) on Review &
# Publish. Bundled in the same PR: the Domain combobox now shows the picked
# option's label instead of its raw enum value after a reload -- domain
# values are upper-snake-case (PromptDomain, e.g. HEALTHCARE_AND_MEDICINE)
# and labels are Title Case, so the two are never equal, making this a real,
# not cosmetic-only, regression if selectedValue goes back to the raw value.
#
# No backend change here: maxTokens already exists on the AI model schema
# (DataSpaceBackend aimodel_schema.py); this PR only wires up a UI control
# for it. One throwaway AI model draft, deleted at teardown.
#
# UNVERIFIED -- not executed. This needs a real login (test_credentials) this
# cloud run has no credentials for, and the PR is not deployed anywhere yet
# (DataSpaceFrontend#558 merged to dev, but the deploy that was supposed to
# ship it failed -- Deploy DataSpace run 45364038485, conclusion failure).
# See the PR body for exactly what to re-check once both are true.

import pytest

from pages.home_page import HomePage


@pytest.fixture
def model(driver, base_url, test_credentials, delete_draft_after):
    email, password = test_credentials
    driver.delete_all_cookies()
    home = HomePage(driver, base_url)
    home.load()
    dash = home.go_to_login(flow="provider", email=email, password=password).goto_my_dashboard()
    page = dash.click_ai_models_card().click_add_new_ai_model()
    delete_draft_after(driver.current_url)
    return page.go_to_details()


@pytest.mark.functional
@pytest.mark.timeout(300)
def test_selected_max_tokens_is_shown_formatted_on_review_and_publish(model):
    model.select_max_tokens("16384")
    model.go_to_publish()
    assert model.review_value("MAXIMUM TOKENS") == "16,384", "not shown with a thousands separator"


@pytest.mark.functional
@pytest.mark.timeout(300)
def test_domain_reopens_showing_the_label_not_the_raw_enum_value(model, driver):
    options = [o for o in model.get_domain_option_values() if o and "select from dropdown" not in o.lower()]
    if not options:
        pytest.skip("Domain combobox has no real option to pick on this backend")
    label = options[0]
    model.select_domain(label)

    driver.refresh()
    model.go_to_details()
    shown = model.get_domain_value()
    assert shown == label, (
        f"Domain shows {shown!r} after a reload, not the picked label {label!r} "
        "(DataSpaceFrontend#558: a raw PromptDomain value here, e.g. upper-snake-case, "
        "means selectedValue regressed back to formData.domain)"
    )
