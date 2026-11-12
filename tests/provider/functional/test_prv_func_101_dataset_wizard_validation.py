# tests/provider/functional/test_prv_func_101_dataset_wizard_validation.py
#
# Dataset wizard (Data Files / Prompt Files -> Metadata -> Review & Publish):
# step gating, inline messages, field limits and what survives a reload.
# One data draft and one prompt draft are shared by the module (qa_drafts).

import os
import shutil
import uuid

import pytest

from pages.provider.create_dataset_page import CreateDatasetPage

pytestmark = pytest.mark.functional

QA_TAG = "[qa-matrix]"
SAMPLE_LICENSES = [
    "Government Open Data License",
    "CC BY 4.0 (Attribution)",
    "Open Database License",
    "CC BY-NC-ND 4.0",
    "CC0 1.0",
    "PDDL 1.0",
]
PROMPT_FORMATS = ["Instruction", "Chat", "Completion", "Few-shot", "Chain of thought", "Zero-shot", "Other"]


def _unique_copy(src, tmp_path, stem):
    dst = tmp_path / f"{stem}_{uuid.uuid4().hex[:8]}{os.path.splitext(src)[1]}"
    shutil.copy(src, dst)
    return str(dst)


def _open(drafts, key, my_dash, driver) -> CreateDatasetPage:
    """Open the shared `key` draft ('data' or 'prompt'), creating it on first use."""
    if key not in drafts:
        url = drafts.create(key, driver)
        if url:
            drafts[key] = url
            driver.get(url)
            return CreateDatasetPage(driver).open_step_url("metadata")
        page = my_dash.click_add_new_prompt_dataset() if key == "prompt" else my_dash.click_add_new_dataset()
        drafts[key] = driver.current_url
        return page
    driver.get(drafts[key])
    return CreateDatasetPage(driver).open_step_url(drafts[key].rsplit("/", 1)[1])


def _with_file(drafts, key, my_dash, driver, csv, tmp_path) -> CreateDatasetPage:
    page = _open(drafts, key, my_dash, driver)
    if not page.get_uploaded_resource_names():
        page.upload_datafile(_unique_copy(csv, tmp_path, key))
    return page


# ─── Data Files ─────────────────────────────────────────────────────────────

def test_prv_func_101_01_metadata_locked_until_file_uploaded(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, "data", provider_dashboard, driver)

    page.press_step("Metadata")
    assert "/edit/resources" in driver.current_url, "The Metadata step opened with no file uploaded"
    assert "Add at least one dataset file to continue." in page.get_inline_errors()
    assert "Incomplete" in page.get_step_text("Data Files")

    page.press_continue()
    assert "/edit/resources" in driver.current_url, "Continue left Data Files with no file uploaded"


def test_prv_func_101_02_unsupported_file_types_not_added(driver, provider_dashboard, qa_drafts, tmp_path):
    exe = tmp_path / "qa_matrix.exe"
    exe.write_bytes(b"MZ not really a program")
    png = shutil.copy(os.path.join("tests", "data", "sample_logo.png"), tmp_path / "qa_matrix.png")
    page = _open(qa_drafts, "data", provider_dashboard, driver)

    page.send_files(str(exe), str(png))
    page.wait_until_saved()

    names = page.get_uploaded_resource_names()
    assert "qa_matrix.exe" not in names and "qa_matrix.png" not in names, f"Unsupported files were listed: {names}"


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#529: Unsupported file types are dropped silently: no error tells the user why")
def test_prv_func_101_03_unsupported_file_type_shows_error(driver, provider_dashboard, qa_drafts, tmp_path):
    exe = tmp_path / "qa_matrix.exe"
    exe.write_bytes(b"MZ not really a program")
    page = _open(qa_drafts, "data", provider_dashboard, driver)

    page.send_files(str(exe))

    text = page.get_page_text().lower()
    assert any(w in text for w in ("not supported", "unsupported", "invalid", "not allowed")), (
        "No message after choosing a .exe file"
    )


def test_prv_func_101_04_multiple_upload_and_delete_card(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    a = _unique_copy(sample_csv_path, tmp_path, "qa_a")
    b = _unique_copy(sample_csv_path, tmp_path, "qa_b")
    page = _open(qa_drafts, "data", provider_dashboard, driver)

    page.upload_datafiles(a, b)
    names = page.get_uploaded_resource_names()
    assert {os.path.basename(a), os.path.basename(b)} <= set(names), f"Both files should be listed: {names}"
    assert "Completed" in page.get_step_text("Data Files")

    page.delete_file(os.path.basename(b))
    page.open_step_url("resources")
    names = page.get_uploaded_resource_names()
    assert os.path.basename(a) in names and os.path.basename(b) not in names, f"After deleting b, got {names}"


# ─── Metadata ───────────────────────────────────────────────────────────────

def test_prv_func_101_05_metadata_required_fields_gate_continue(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.press_continue()
    assert "/edit/metadata" in driver.current_url, "Continue left an empty Metadata step"
    errors = page.get_inline_errors()
    for msg in ("Description is required", "Sector is required", "Tags are required"):
        assert msg in errors, f"Missing {msg!r}; shown: {errors}"
    assert "Incomplete" in page.get_step_text("Metadata")

    page.press_step("Review & Publish")
    assert "/edit/metadata" in driver.current_url, "The Review step opened from an incomplete Metadata step"


def test_prv_func_101_06_publish_blocked_while_metadata_incomplete(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)

    page.open_step_url("publish")  # by URL: the stepper itself refuses to go here
    assert "Incomplete" in page.get_step_text("Metadata")
    assert not page.is_publish_enabled(), "Publish Dataset is enabled with no description, sector or tags"


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#529: Dataset Review & Publish shows '—' for missing fields but no list of what to fix (the use case review has one)")
def test_prv_func_101_07_review_lists_missing_items(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)

    page.open_step_url("publish")
    text = page.get_page_text()
    assert "description" in text.lower() and "Fix" in text.split(), "No list of missing items on the review step"


def test_prv_func_101_08_access_type_options(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    access = page.get_access_types()
    assert set(access) == {"PUBLIC", "RESTRICTED"}, access
    assert access["PUBLIC"]["checked"] and not access["PUBLIC"]["disabled"]
    assert access["RESTRICTED"]["disabled"] and access["RESTRICTED"]["title"] == "Coming Soon", access["RESTRICTED"]


def test_prv_func_101_09_license_options_selectable(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    options = page.get_license_options()
    assert len(options) >= 50 and set(SAMPLE_LICENSES) <= set(options), f"License options: {options}"
    for lic in SAMPLE_LICENSES:
        page.select_license(lic)
        assert page.get_selected_license_text() == lic


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#528: Choosing a License triggers no autosave; after a reload it is back to 'Select a license' (cf. DataSpaceBackend#291)")
def test_prv_func_101_09b_license_persists_after_reload(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    for lic in SAMPLE_LICENSES[:2]:
        page.select_license(lic)
        page.open_step_url("metadata")
        assert page.get_selected_license_text() == lic, f"{lic!r} did not survive a reload"


def test_prv_func_101_10_unicode_title_persists(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    title = f"Ünïcödé डेटा 数据 🚀 {QA_TAG}"
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.set_title(title)
    page.open_step_url("metadata")
    assert page.get_title_value() == title


def test_prv_func_101_11_long_title_within_limit_persists(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    title = (QA_TAG + " " + "T" * 300)[:255]
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.set_title(title)
    page.open_step_url("metadata")
    assert page.get_title_value() == title


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#528: A 400-char title shows 'All changes saved' but is silently not saved; no limit or error shown")
def test_prv_func_101_12_over_long_title_rejected_visibly(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    title = QA_TAG + " " + "L" * 400
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.set_title(title)
    error_shown = bool(page.get_inline_errors())
    page.open_step_url("metadata")
    assert error_shown or page.get_title_value() == title, "Over-long title was dropped without any message"


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#529: The description counter counts the editor's HTML: 1001 typed chars show as 1008/1000")
def test_prv_func_101_13_description_counter_shows_over_limit(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.enter_description("D" * 1001)
    assert page.get_description_counter() == "Character limit: 1001/1000"


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#528: A description over 1000 chars shows 'All changes saved' and no error, but is not saved")
def test_prv_func_101_14_over_limit_description_rejected_visibly(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    text = "E" * 1001
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.enter_description(text)
    page.wait_for_autosave()
    error_shown = bool(page.get_inline_errors())
    page.open_step_url("metadata")
    assert error_shown or page.get_description_value() == text, "Over-limit description was dropped without any message"


def test_prv_func_101_15_complete_metadata_opens_review_and_previous_keeps_values(
        driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path, sector_name):
    desc = f"{QA_TAG} wizard validation"
    page = _with_file(qa_drafts, "data", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()
    page.enter_description(desc)
    if sector_name not in page.get_selected_sectors():
        page.select_sectors([sector_name])
    if "Finance" not in page.get_selected_tags():
        page.select_tags(["Finance"])

    page.click_continue("publish")
    assert "Completed" in page.get_step_text("Metadata")
    assert page.is_publish_enabled(), "Publish Dataset stayed disabled with every required field filled"

    page.click_previous("metadata")
    assert page.get_description_value() == desc
    assert sector_name in page.get_selected_sectors()
    assert "Finance" in page.get_selected_tags()


# ─── Prompt dataset ─────────────────────────────────────────────────────────

def test_prv_func_101_16_prompt_files_required(driver, provider_dashboard, qa_drafts):
    page = _open(qa_drafts, "prompt", provider_dashboard, driver)

    page.press_continue()
    assert "/edit/resources" in driver.current_url
    assert "Add at least one prompt file to continue." in page.get_inline_errors()


def test_prv_func_101_17_prompt_format_options_selectable(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "prompt", provider_dashboard, driver, sample_csv_path, tmp_path)
    name = page.get_uploaded_resource_names()[0]
    page.open_file_details(name)

    assert page.get_prompt_field_options("Prompt Format") == PROMPT_FORMATS
    page.close_file_details().open_file_details(name)  # Escape out of the list closes the sheet
    for fmt in PROMPT_FORMATS:
        page.select_prompt_format(fmt)
        assert page.get_prompt_format() == fmt


def test_prv_func_101_18_prompt_format_persists(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "prompt", provider_dashboard, driver, sample_csv_path, tmp_path)
    name = page.get_uploaded_resource_names()[0]

    for fmt in ("Few-shot", "Chain of thought"):
        page.open_file_details(name).select_prompt_format(fmt)
        page.wait_until_saved()
        page.open_step_url("resources").open_file_details(name)
        assert page.get_prompt_format() == fmt, f"{fmt!r} did not survive a reload"
        page.close_file_details()


def test_prv_func_101_19_prompt_metadata_required_fields(driver, provider_dashboard, qa_drafts, sample_csv_path, tmp_path):
    page = _with_file(qa_drafts, "prompt", provider_dashboard, driver, sample_csv_path, tmp_path)
    page.go_to_metadata_tab()

    page.press_continue()
    assert "/edit/metadata" in driver.current_url
    errors = page.get_inline_errors()
    for msg in ("Task Type is required", "Domain is required",
                "Target Languages are required", "Target Model Types are required"):
        assert msg in errors, f"Missing {msg!r}; shown: {errors}"

    page.open_step_url("publish")
    assert not page.is_publish_enabled(), "Publish Dataset is enabled for an incomplete prompt dataset"
