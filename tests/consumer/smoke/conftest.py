# tests/consumer/smoke/conftest.py
#
# A handful of consumer/smoke tests need to create and publish a record (via
# GraphQL) before checking how the public page renders it. Re-export the
# existing API auth/client fixtures from tests/api/conftest.py instead of
# re-implementing the Keycloak -> Django JWT exchange here.

from tests.api.conftest import (  # noqa: F401
    anon_graphql_client,
    api_base_url,
    auth_token,
    graphql_client,
    keycloak_config,
)
