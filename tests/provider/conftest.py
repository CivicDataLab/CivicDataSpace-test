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
