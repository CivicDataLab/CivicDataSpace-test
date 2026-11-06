# tests/provider/functional/test_prv_func_201_collaborative_wizard_validation.py
#
# Collaborative wizard (About -> People -> Content -> Review & Publish):
# required-field gating, subdomain and link validation, values kept across steps.

import pytest

from pages.home_page import HomePage
from tests.data.test_data import CollaborativeTestData

ABOUT_MESSAGES = ["Add a description to continue", "Select at least one sector", "Select at least one SDG goal"]
CONTENT_MESSAGE = "Add at least one dataset or use case to continue."
RESERVED = "This subdomain is reserved. Choose another."


def new_draft(driver, base_url, test_credentials, delete_draft_after):
    email, password = test_credentials
    driver.delete_all_cookies()
    home = HomePage(driver, base_url)
    home.load()
    dash = home.go_to_login(flow="provider", email=email, password=password).goto_my_dashboard()
    page = dash.click_collaboratives_card().click_add_new_collaborative()
    page.page_text()
    delete_draft_after(driver.current_url)
    return page


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_201a_required_fields_block_continue_and_publish(driver, base_url, test_credentials, delete_draft_after):
    """An empty draft cannot leave About or be published, and Review lists every gap."""
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)

    page.press_continue()
    for msg in ABOUT_MESSAGES:
        assert page.is_text_shown(msg), f"About did not show {msg!r} after Continue"
    assert driver.current_url.endswith("/about"), "Continue left About with the required fields empty"

    page.open_step("publish")
    review = page.page_text()
    for msg in ABOUT_MESSAGES + [CONTENT_MESSAGE]:
        assert msg in review, f"Review & Publish does not list {msg!r}:\n{review}"

    page.press_publish()
    assert page.is_text_shown(CONTENT_MESSAGE, timeout=5)
    assert "/edit/" in driver.current_url, "Publish Collaborative published an incomplete draft"


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_201b_subdomain_validation(driver, base_url, test_credentials, delete_draft_after):
    """The subdomain is slugified, reserved names are refused, and the public address follows it."""
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)

    page.enter_slug("QA Matrix Slug!!")
    assert page.get_slug_value() == "qa-matrix-slug", f"Slug not normalised: {page.get_slug_value()!r}"
    assert page.get_public_address().startswith("https://qa-matrix-slug."), page.get_public_address()
    assert not page.is_text_shown(RESERVED, timeout=2)

    for reserved in ("admin", "www"):
        page.enter_slug(reserved)
        assert page.is_text_shown(RESERVED), f"{reserved!r} was not flagged as reserved"


@pytest.mark.functional
@pytest.mark.timeout(420)
@pytest.mark.xfail(strict=True, reason="Subdomain accepts 80 characters; a DNS label is at most 63 (DataSpaceBackend#292 validation gaps)")
def test_prv_func_201c_subdomain_length_limit(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.enter_slug("a" * 80)
    assert len(page.get_slug_value()) <= 63, f"Slug kept {len(page.get_slug_value())} characters with no error"


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_201d_external_link_rejects_invalid_url(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.enter_platform_url("not a url")
    assert page.get_platform_url_validation_message(), "External Link accepted 'not a url' as a valid URL"
    page.enter_platform_url("https://example.org/qa-matrix")
    assert page.get_platform_url_validation_message() == ""


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_201e_invalid_external_link_not_saved(driver, base_url, test_credentials, delete_draft_after):
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.enter_platform_url("not a url")
    page.reload()
    page.page_text()
    assert page.get_platform_url_value() == "", f"Invalid link persisted: {page.get_platform_url_value()!r}"


@pytest.mark.functional
@pytest.mark.timeout(600)
def test_prv_func_201f_unicode_values_persist_across_steps_and_reload(
        driver, base_url, test_credentials, delete_draft_after, sector_name):
    """About filled with Unicode passes the gate; People is optional; Content still needs an item."""
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    title = "[qa-matrix] सहयोग 協作 Café 🚀"
    description = "QA matrix — विवरण 説明 ✓"

    page.edit_collaborative_name(title)
    page.enter_description(description)
    page.select_sectors([sector_name])
    page.select_sdg_goals(CollaborativeTestData.SDG_GOALS)

    page.click_continue("people")
    page.click_continue("content")  # People is optional
    page.press_continue()
    assert driver.current_url.endswith("/content"), "Content let Continue through with nothing connected"

    page.open_step("about")
    page.page_text()
    assert page.get_collaborative_name_value() == title
    assert page.get_description_value() == description
    assert sector_name in page.get_selected_sectors()
    assert CollaborativeTestData.SDG_GOALS in page.get_selected_sdg_goals()

    page.reload()
    page.page_text()
    assert page.get_collaborative_name_value() == title, "Unicode title lost after reload"
    assert page.get_description_value() == description, "Unicode description lost after reload"

    page.open_step("publish")
    review = page.page_text()
    assert CONTENT_MESSAGE in review
    for msg in ABOUT_MESSAGES:
        assert msg not in review, f"Review still lists {msg!r} after About was filled"
