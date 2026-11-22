# tests/provider/functional/test_prv_func_207_dataset_platform_import.py
#
# DataSpace#251 (frontend for #174, backend DataSpaceBackend#204): on a draft's
# Data Files step, Public Platform > GitHub > URL > Generate creates a new draft
# prefilled from GitHub, with one external file linking back. Functional: the
# backend calls GitHub live. Both drafts are deleted at teardown.

import pytest

from pages.provider.create_dataset_page import CreateDatasetPage
from tests.provider.smoke.test_prv_021_wizard_validation import _open_step

pytestmark = [pytest.mark.functional]

URL = "https://github.com/datasets/gdp"  # long-lived public repo; the API test imports a different one
SOURCE = "query($id: UUID!){ getDataset(datasetId:$id){ status source { platform sourceUrl } } }"


def test_prv_func_207_generate_from_github(driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_func_207_generate_from_github
    Steps:
      1. New draft via the API; open its Data Files step
      2. Public Platform > GitHub > paste the repository URL > Generate
      3. A new draft opens, the success toast shows, and its files list the GitHub link
      4. The API records the draft's source as that GitHub repository
    """
    own = provider_api.gql("{ datasets(pagination:{limit:100}) { source { sourceUrl } } }")["data"]["datasets"]
    if any((d.get("source") or {}).get("sourceUrl") == URL for d in own):
        pytest.skip(f"This account already holds an import of {URL}; a second one is refused by design")

    _open_step("dataset", "resources", driver, open_listing, provider_api, cleanup)
    original = driver.current_url.split("/dataset/")[1].split("/")[0]
    page = CreateDatasetPage(driver)
    new_id = page.import_from_platform("GitHub", URL)
    cleanup.track("dataset", new_id, None)

    assert new_id != original, "Generate stayed on the same draft"
    assert page.toast_shown("Dataset metadata generated from the platform."), "No success toast after Generate"
    assert page.file_listed("Dataset on GitHub"), "The new draft does not list the GitHub link"
    body = provider_api.gql(SOURCE, {"id": new_id})
    assert "errors" not in body, body["errors"]
    dataset = body["data"]["getDataset"]
    assert dataset["status"] == "DRAFT" and dataset["source"] == {"platform": "GITHUB", "sourceUrl": URL}, dataset
