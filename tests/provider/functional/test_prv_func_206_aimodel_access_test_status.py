# tests/provider/functional/test_prv_func_206_aimodel_access_test_status.py
#
# DataSpaceFrontend#553 / #554: Test All Access Methods names why a Custom API
# call failed, and See details shows the provider's HTTP response. The browser
# calls the provider itself, so each access method points at a stubbed host
# that answers with the status in its path (utils.browser_network); nothing
# leaves the browser.

import pytest

from tests.provider.functional.test_prv_func_202_aimodel_wizard_validation import new_draft
from utils.browser_network import STUB_HOST, stub_fetch_statuses

pytestmark = [pytest.mark.functional, pytest.mark.deployed_pr("DataSpaceFrontend#554", site="HOME_URL_DEV")]

# access method -> (stubbed response, label shown, text in See details)
CASES = {
    "qa-429": ("429", "Rate Limit Exceeded", "HTTP 429"),
    "qa-429-quota": ("429/quota", "Quota Exhausted", "insufficient_quota"),
    "qa-402": ("402", "Quota Exhausted", "HTTP 402"),
    "qa-503": ("503", "Provider Error", "HTTP 503"),
    "qa-404": ("404", "Invalid Request Configuration", "HTTP 404"),
    "qa-401": ("401", "Authentication Failed", "HTTP 401"),
}


@pytest.mark.timeout(600)
def test_prv_func_206_access_test_names_the_failure(driver, base_url, test_credentials, delete_draft_after):
    """
    Test Case ID: test_prv_func_206_access_test_names_the_failure
    Steps:
      1. New AI model draft; a version with one Custom API access method per stubbed status
      2. Open the version, enter a Test Input, press Test All Access Methods
      3. Each row shows its status label, and See details shows the HTTP response
    """
    stub_fetch_statuses(driver)
    page = new_draft(driver, base_url, test_credentials, delete_draft_after)
    page.add_version_with_methods("1.0", [(name, "qa-model", f"https://{STUB_HOST}/{resp}") for name, (resp, _, _) in CASES.items()])
    page.open_version("1.0").run_access_tests("hello")

    wrong = {name: page.access_test_status(name) for name, (_, label, _) in CASES.items() if page.access_test_status(name) != label}
    assert not wrong, f"Wrong status label (got): {wrong}"
    missing = {name: detail for name, (_, _, detail) in CASES.items() if detail not in page.access_test_detail(name)}
    assert not missing, f"See details does not show: {missing}"
