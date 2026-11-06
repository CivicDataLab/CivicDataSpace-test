# tests/provider/functional/test_prv_func_202_aimodel_wizard_validation.py
#
# AI model wizard (Versions -> Model Information -> Review & Publish): the
# version sheet's controls and what each choice reveals, and the Model
# Information fields that gate Review & Publish. No real credentials: any key
# field gets a dummy value.

import pytest

from pages.home_page import HomePage
from locators.provider.ai_models_locators import AiModelsLocators as L

LIFECYCLE_STAGES = ["Development", "Testing", "Beta Testing", "Staging", "Production", "Deprecated", "Retired"]

# Provider Type -> the named fields its access method form shows.
PROVIDER_FIELDS = {
    "OpenAI": ["providerModelId", "apiKey"],
    "Ollama": ["providerModelId", "apiEndpointUrl"],
    "Together AI": ["providerModelId", "apiKey"],
    "Replicate": ["providerModelId", "apiKey"],
    "Custom API": ["providerModelId", "apiEndpointUrl", "apiRequestTemplate", "apiResponsePath", "apiTimeoutSeconds"],
}
PROVIDER_KEY_LABEL = {"OpenAI": "OpenAI API Key", "Together AI": "Together AI API Key", "Replicate": "Replicate API Token"}

# Custom API Authentication Type -> extra fields and their labels.
AUTH_FIELDS = {
    "None": ([], []),
    "Bearer Token": (["apiAuthHeaderName", "apiKey"], ["Bearer Token"]),
    "API Key": (["apiAuthHeaderName", "apiKey"], ["Header or Parameter Name", "Send key in", "API Key"]),
    "Custom Header": (["apiAuthHeaderName", "apiKey"], ["Header Name", "Header Value"]),
}

REVIEW_MESSAGES = {
    "domain": "Select a domain.",
    "description": "Add a description of the model.",
    "sector": "Select at least one sector.",
    "language": "Define how language support applies to this model.",
    "license": "Select a usage license.",
}


def new_draft(driver, base_url, test_credentials, delete_draft_after):
    email, password = test_credentials
    driver.delete_all_cookies()
    home = HomePage(driver, base_url)
    home.load()
    dash = home.go_to_login(flow="provider", email=email, password=password).goto_my_dashboard()
    page = dash.click_ai_models_card().click_add_new_ai_model()
    page.page_text()
    delete_draft_after(driver.current_url)
    return page


@pytest.mark.functional
@pytest.mark.timeout(600)
def test_prv_func_202a_version_sheet_options_change_fields(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet()

    assert page.sheet_select_options(L.LIFECYCLE_SELECT) == LIFECYCLE_STAGES
    for stage in LIFECYCLE_STAGES:
        page.pick_sheet_option(L.LIFECYCLE_SELECT, stage)
        assert page.get_sheet_select_value(L.LIFECYCLE_SELECT) == stage

    page.open_access_form()
    assert page.sheet_select_options(L.PROVIDER_TYPE_SELECT) == list(PROVIDER_FIELDS)
    for provider, fields in PROVIDER_FIELDS.items():
        page.pick_sheet_option(L.PROVIDER_TYPE_SELECT, provider)
        shown = page.sheet_field_names()
        for f in fields:
            assert f in shown, f"{provider}: field {f!r} missing, form shows {shown}"
        if provider in PROVIDER_KEY_LABEL:
            assert PROVIDER_KEY_LABEL[provider] in page.sheet_labels()
            assert "apiEndpointUrl" not in shown, f"{provider} shows an endpoint field"
        else:
            assert "apiKey" not in shown, f"{provider} shows an API key field"

    # Custom API is selected last: its auth type decides the credential fields.
    assert page.sheet_select_options(L.AUTH_TYPE_SELECT) == list(AUTH_FIELDS)
    for auth, (fields, labels) in AUTH_FIELDS.items():
        page.pick_sheet_option(L.AUTH_TYPE_SELECT, auth)
        shown, shown_labels = page.sheet_field_names(), page.sheet_labels()
        for f in fields:
            assert f in shown, f"Auth {auth}: field {f!r} missing, form shows {shown}"
        for lbl in labels:
            assert lbl in shown_labels, f"Auth {auth}: label {lbl!r} missing, form shows {shown_labels}"
        if not fields:
            assert "apiKey" not in shown and "apiAuthHeaderName" not in shown

    page.fill_sheet_field("apiKey", "qa-dummy-key")
    assert page.sheet_field_validation_message("apiKey") == ""


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_202b_access_method_required_fields(driver, base_url, test_credentials, delete_draft_after):
    """A Custom API access method is not added while its required fields are empty."""
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet().open_access_form()
    page.pick_sheet_option(L.PROVIDER_TYPE_SELECT, "Custom API")
    page.press_add_access_method()
    assert page.is_access_form_open(), "Add Access Method closed the form with every field empty"
    for f in ("accessName", "providerModelId", "apiEndpointUrl"):
        assert page.sheet_field_validation_message(f), f"{f} is not flagged as required"


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_202c_invalid_endpoint_url_rejected(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet().open_access_form()
    page.pick_sheet_option(L.PROVIDER_TYPE_SELECT, "Custom API")
    page.fill_sheet_field("accessName", "[qa-matrix] bad url")
    page.fill_sheet_field("providerModelId", "qa-model")
    page.fill_sheet_field("apiEndpointUrl", "not-a-url")
    page.press_add_access_method()
    assert page.is_access_form_open(), "An access method with endpoint 'not-a-url' was added"


@pytest.mark.functional
@pytest.mark.timeout(420)
@pytest.mark.xfail(strict=True, reason="Timeout (seconds) has no bounds: 0, -5 and 100000 are all valid (DataSpaceBackend#292 negatives)")
def test_prv_func_202d_timeout_bounds(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet().open_access_form()
    page.pick_sheet_option(L.PROVIDER_TYPE_SELECT, "Custom API")
    accepted = []
    for value in ("0", "-5", "100000"):
        page.fill_sheet_field("apiTimeoutSeconds", value)
        if not page.sheet_field_validation_message("apiTimeoutSeconds"):
            accepted.append(value)
    assert not accepted, f"Timeout accepted out-of-range values {accepted}"


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_202e_duplicate_version_name_refused(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet().enter_version_name("1.0").press_save_version()
    assert page.is_version_saved(), "Version 1.0 was not saved"
    page.cancel_version_sheet()
    page.open_version_sheet().enter_version_name("1.0").press_save_version()
    assert not page.is_version_saved(timeout=8), "A second version named 1.0 was saved"
    page.cancel_version_sheet().reload()
    page.page_text()
    assert page.listed_versions().count("Version 1.0") == 1, f"Duplicate version saved: {page.listed_versions()}"


@pytest.mark.functional
@pytest.mark.timeout(420)
@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#530: Save Version with an empty Version Name saves a version (named 1.0) instead of asking for a name")
def test_prv_func_202f_version_name_required(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet().press_save_version()
    assert not page.is_version_saved(timeout=8), "Save Version saved a version with no name"
    page.cancel_version_sheet().reload()
    page.page_text()
    assert page.listed_versions() == [], f"A version was saved without a name: {page.listed_versions()}"


@pytest.mark.functional
@pytest.mark.timeout(720)
def test_prv_func_202g_model_information_gates_review(driver, base_url, test_credentials, delete_draft_after, sector_name):
    """Each required Model Information field removes exactly its own Review item."""
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.go_to_details()

    domains = page.get_domain_option_values()
    assert len(domains) >= 5 and "Agriculture" in domains, f"Domain options look unpopulated: {domains}"

    page.open_step("publish")
    review = page.page_text()
    for msg in REVIEW_MESSAGES.values():
        assert msg in review, f"Review does not list {msg!r}:\n{review}"
    page.press_publish()
    assert "/edit/" in driver.current_url, "Publish AI Model published an empty draft"

    steps = [
        ("domain", lambda: page.select_domain("Agriculture")),
        # Intended Use is typed after the description because the description alone
        # is not autosaved (see 202h).
        ("description", lambda: (page.enter_description("[qa-matrix] model description ✓"),
                                 page.enter_intended_use("[qa-matrix] intended use"))),
        ("sector", lambda: page.select_sectors([sector_name])),
        ("language", lambda: page.select_languages(["English"])),
        ("license", lambda: page.select_usage_license("MIT License")),
    ]
    done = []
    for key, fill in steps:
        page.open_step("details")
        page.page_text()
        fill()
        page.wait_for_autosave()
        done.append(key)
        page.open_step("publish")
        review = page.page_text()
        for k, msg in REVIEW_MESSAGES.items():
            if k in done:
                assert msg not in review, f"{msg!r} still listed after filling {key}"
            else:
                assert msg in review, f"{msg!r} vanished after filling only {done}"


@pytest.mark.functional
@pytest.mark.timeout(420)
@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#530: Model Information: a Description edited on its own is never autosaved; it is lost on reload unless another field is changed afterwards")
def test_prv_func_202h_description_alone_is_autosaved(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.go_to_details()
    page.enter_description("[qa-matrix] description only")
    page.wait_for_autosave()
    page.reload()
    page.page_text()
    assert page.get_description_text() == "[qa-matrix] description only"


@pytest.mark.functional
@pytest.mark.timeout(420)
@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#530: Cancel on the Add Version sheet does not discard: a half-filled access method already created 'Version 1.0'")
def test_prv_func_202i_cancel_discards_new_version(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.open_version_sheet()
    page.pick_sheet_option(L.LIFECYCLE_SELECT, "Testing")
    page.open_access_form()
    page.pick_sheet_option(L.PROVIDER_TYPE_SELECT, "Custom API")
    page.pick_sheet_option(L.AUTH_TYPE_SELECT, "Bearer Token")
    page.fill_sheet_field("apiKey", "qa-dummy-key")
    page.cancel_version_sheet().reload()
    page.page_text()
    assert page.listed_versions() == [], f"Cancel kept a version: {page.listed_versions()}"
