# tests/provider/functional/test_prv_func_102_usecase_wizard_validation.py
#
# Use case wizard (Builder -> Connect -> Review & Publish): what each step
# requires, the messages it shows, and what survives navigation and reloads.
# One draft is shared by the module (qa_drafts) and deleted afterwards.

import pytest

from pages.provider.create_usecase_page import CreateUsecasePage

pytestmark = pytest.mark.functional

QA_TAG = "[qa-matrix]"
DATASET_SEARCH = "Search published datasets..."


def _open(drafts, my_dash, driver, step=None) -> CreateUsecasePage:
    """Open the shared draft (at `step`), creating it on first use."""
    if "uc" not in drafts:
        page = my_dash.click_usecases_card().click_add_new_usecase()
        drafts["uc"] = driver.current_url
    else:
        driver.get(drafts["uc"])
        page = CreateUsecasePage(driver)
    return page.open_step_url(step) if step else page.open_step_url("builder")


def test_prv_func_102_01_builder_requires_thumbnail(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, provider_dashboard, driver)

    page.press_continue()
    assert "/builder" in driver.current_url, "Continue left Builder with no thumbnail"
    assert "Upload a thumbnail image" in page.get_inline_errors()
    assert "Incomplete" in page.get_step_text("Builder")


def test_prv_func_102_02_review_lists_missing_items_and_blocks_publish(
        driver, provider_dashboard, qa_drafts, sample_logo_path):
    page = _open(qa_drafts, provider_dashboard, driver)
    page.upload_thumbnail(sample_logo_path)

    page.open_step_url("publish")
    text = page.get_page_text()
    for msg in ("Needs attention", "Add at least one content block.", "Select at least one sector.",
                "Select at least one SDG goal.", "Connect at least one dataset."):
        assert msg in text, f"Review step does not list {msg!r}"
    assert not page.is_publish_enabled(), "Publish Use Case is enabled with items missing"


def test_prv_func_102_03_unicode_title_previous_continue_and_reload_keep_values(
        driver, provider_dashboard, qa_drafts, sample_logo_path):
    title = f"Ünïcödé उपयोग 用例 🚀 {QA_TAG}"
    subtitle = "Subtitle — ñ, ü, 😀"
    page = _open(qa_drafts, provider_dashboard, driver)
    page.enter_title(title).enter_subtitle(subtitle)

    page.click_continue("connect")
    page.click_previous("builder")
    assert page.get_title_value() == title
    assert page.get_subtitle_value() == subtitle

    page.open_step_url("builder")
    assert page.get_title_value() == title, "Title did not survive a reload"
    assert page.get_subtitle_value() == subtitle, "Subtitle did not survive a reload"


def test_prv_func_102_04_connect_required_fields(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, provider_dashboard, driver, "connect")

    page.press_continue()
    assert "/connect" in driver.current_url, "Continue left an empty Connect step"
    text = page.get_page_text()
    for msg in ("Select at least one SDG goal", "Select at least one sector", "Connect at least one dataset"):
        assert msg in text, f"Connect step does not show {msg!r}"


def test_prv_func_102_05_dataset_search_no_results(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, provider_dashboard, driver, "connect")

    page.search_picker(DATASET_SEARCH, "zzqq-no-such-dataset-xyz")
    assert page.get_picker_empty_text() == "No matches found."


def test_prv_func_102_06_connect_and_remove_dataset(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, provider_dashboard, driver, "connect")

    title = page.connect_first_dataset()
    page.open_step_url("connect")
    assert page.is_connected("Datasets", title), f"'{title}' was not connected after a reload"

    page.remove_connected(title)
    page.open_step_url("connect")
    assert not page.is_connected("Datasets", title), f"'{title}' came back after removing it"


def test_prv_func_102_07_tags_add_remove_persist(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, provider_dashboard, driver, "connect")

    page.select_tags(["Finance", "Budget"])
    assert {"Finance", "Budget"} <= set(page.get_selected_tags())

    page.remove_chip("Tags", "Budget")
    page.open_step_url("connect")
    tags = page.get_selected_tags()
    assert "Finance" in tags and "Budget" not in tags, f"Tags after reload: {tags}"


def test_prv_func_102_08_sdg_and_geography_multi_select_persist(driver, provider_dashboard, qa_drafts):
    sdgs = ["01. No Poverty", "13. Climate Action"]
    page = _open(qa_drafts, provider_dashboard, driver, "connect")

    page.select_field_options("SDG Goals", sdgs)
    page.select_geography("Assam")
    page.select_geography("Bihar")
    before = " ".join(page.get_selected_geography())
    assert "Assam" in before and "Bihar" in before, f"Both geographies should show before reload: {before}"

    page.open_step_url("connect")
    assert set(sdgs) <= set(page.get_selected_sdg_goals()), page.get_selected_sdg_goals()
    geos = " ".join(page.get_selected_geography())
    assert "Assam" in geos and "Bihar" in geos, geos


def test_prv_func_102_09_review_updates_as_items_are_fixed(driver, provider_dashboard, qa_drafts, sector_name):
    page = _open(qa_drafts, provider_dashboard, driver, "connect")
    if sector_name not in page.get_selected_sectors():
        page.select_sectors([sector_name])

    page.open_step_url("publish")
    text = page.get_page_text()
    assert "Select at least one sector." not in text and "Select at least one SDG goal." not in text
    assert "Connect at least one dataset." in text and "Add at least one content block." in text
    assert not page.is_publish_enabled()
