# tests/provider/conftest.py
#
# Fixtures shared by the provider UI tests.

import pytest

from utils.provider_api import Cleanup, ProviderAPI


@pytest.fixture(scope="session")
def provider_api(test_credentials):
    """GraphQL access as the account this worker logs in with.

    Authenticating happens before any test body runs, so a test that cannot
    clean up after itself is skipped instead of leaving records behind.
    """
    email, password = test_credentials
    return ProviderAPI(email, password)


@pytest.fixture
def cleanup(provider_api):
    """Registry of records the test creates; everything is deleted on teardown.

    Teardown runs after a failed test as well, and raises when a record could
    not be deleted, so leftover data fails the run instead of accumulating.
    """
    registry = Cleanup(provider_api)
    yield registry
    registry.run()


@pytest.fixture
def open_listing(driver, logged_in_provider, request):
    """Log in and open one dashboard listing, as the individual or as the org's admin.

    Returns a callable `open_listing(scope, section)` -> ListingTablePage, where
    `scope` is 'individual' or 'org' (the account's dedicated `writable_org`).
    """
    from pages.provider.listing_table_page import ListingTablePage

    def _open(scope, section):
        if scope == "org":
            logged_in_provider.goto_organizations().select_org(request.getfixturevalue("writable_org"))
        else:
            logged_in_provider.goto_my_dashboard()
        return ListingTablePage(driver).open_section(section)

    return _open
