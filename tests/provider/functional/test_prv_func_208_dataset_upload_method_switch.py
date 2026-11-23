# tests/provider/functional/test_prv_func_208_dataset_upload_method_switch.py
#
# DataSpace#259: a dataset takes either uploaded files or an import from a public
# platform, not both. Switching to the other method while one is in use asks first;
# Cancel keeps everything, the confirm clears the old method.

import os
import shutil
import uuid

import pytest

from pages.provider.create_dataset_page import CreateDatasetPage
from tests.provider.smoke.test_prv_021_wizard_validation import _open_step

pytestmark = [pytest.mark.functional]

URL = "https://github.com/datasets/gdp"
RESOURCES = "query($id: UUID!){ getDataset(datasetId:$id){ resources { id } } }"


def _dataset_id(driver):
    return driver.current_url.split("/dataset/")[1].split("/")[0]


def _file_count(provider_api, dataset_id):
    body = provider_api.gql(RESOURCES, {"id": dataset_id})
    assert "errors" not in body, body["errors"]
    return len(body["data"]["getDataset"]["resources"])


def test_prv_func_208_uploaded_files_block_platform_until_cleared(driver, open_listing, provider_api, cleanup, sample_csv_path, tmp_path):
    """
    Test Case ID: test_prv_func_208_uploaded_files_block_platform_until_cleared
    Steps:
      1. Draft with one uploaded file; open Public Platform
      2. A confirm says files were already uploaded; Cancel keeps the file and the File Upload tab
      3. Open Public Platform again and confirm "Clear Files and Switch"
      4. The Public Platform tab shows and the draft has no files left
    """
    _open_step("dataset", "resources", driver, open_listing, provider_api, cleanup)
    dataset_id = _dataset_id(driver)
    copy = str(tmp_path / f"qa_switch_{uuid.uuid4().hex[:8]}.csv")
    shutil.copy(sample_csv_path, copy)
    page = CreateDatasetPage(driver)
    name = page.upload_datafile(copy) and os.path.basename(copy)

    page.press_upload_method_tab("Public Platform")
    assert "already uploaded files" in page.switch_dialog_text(), "No confirm when switching away from uploaded files"
    page.answer_switch_dialog("Cancel")
    assert not page.is_platform_tab_shown(2), "Cancel still switched to Public Platform"
    assert page.file_listed(name) and _file_count(provider_api, dataset_id) == 1, "Cancel dropped the uploaded file"

    page.press_upload_method_tab("Public Platform")
    assert page.switch_dialog_text(), "The confirm did not open the second time"
    page.answer_switch_dialog("Clear Files and Switch")
    assert page.is_platform_tab_shown(), "Confirming did not open Public Platform"
    assert _file_count(provider_api, dataset_id) == 0, "The uploaded file was not cleared"


def test_prv_func_208_platform_url_blocks_upload_until_cleared(driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_func_208_platform_url_blocks_upload_until_cleared
    Steps:
      1. Draft on Data Files; pick GitHub and paste a URL on Public Platform (no Generate)
      2. Open File Upload: a confirm says a platform URL was already entered
      3. Cancel keeps the platform tab and the URL
      4. Open File Upload again and confirm "Clear URL and Switch"; the platform choice is reset
    """
    _open_step("dataset", "resources", driver, open_listing, provider_api, cleanup)
    page = CreateDatasetPage(driver)
    page.fill_platform("GitHub", URL)

    page.press_upload_method_tab("File Upload")
    assert "already entered a public platform URL" in page.switch_dialog_text(), "No confirm when switching away from a platform URL"
    page.answer_switch_dialog("Cancel")
    assert page.get_platform_url() == URL, "Cancel lost the platform URL"

    page.press_upload_method_tab("File Upload")
    assert page.switch_dialog_text(), "The confirm did not open the second time"
    page.answer_switch_dialog("Clear URL and Switch")
    assert not page.is_platform_tab_shown(2), "Confirming did not leave Public Platform"
    page.press_upload_method_tab("Public Platform")
    assert page.is_platform_reset(), "The platform choice survived Clear URL and Switch"
