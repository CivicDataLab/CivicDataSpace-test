# tests/api/client.py
#
# Reusable HTTP clients for DataSpace REST and GraphQL API testing.

from __future__ import annotations

import time

import requests

# Gateway statuses that mean nginx gave up waiting for the backend, not that
# the API answered. Retried rather than asserted on.
GATEWAY_STATUSES = (502, 503, 504)

# Longer than nginx's own 60s proxy timeout, so a slow response arrives as a
# status code instead of a client-side ReadTimeout.
DEFAULT_TIMEOUT = 90
RETRIES = 3


def _request_with_retries(fn, url, **kwargs):
    """Issue a request, retrying only gateway timeouts.

    The dev backend is intermittently slow on authenticated routes - measured
    8.3s, 8.3s and 50.3s on consecutive calls to /api/activities/user/, and
    similar on the token exchange - so requests cross nginx's 60s timeout at
    random and surface as 504. Retrying those keeps an infrastructure problem
    from being reported as an API contract failure.

    Only gateway statuses and transport errors are retried. A 4xx or a 5xx
    raised by the application itself is returned immediately, so genuine
    failures still surface on the first attempt.
    """
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    last_error = None
    for attempt in range(RETRIES):
        try:
            resp = fn(url, **kwargs)
        except requests.RequestException as exc:
            last_error = exc
        else:
            if resp.status_code not in GATEWAY_STATUSES:
                return resp
            last_error = None
        if attempt < RETRIES - 1:
            time.sleep(3)
    if last_error is not None:
        raise last_error
    return resp


class APIClient:
    """
    Thin wrapper around requests.Session for REST API calls.
    All requests include the Authorization header when a token is provided.
    """

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, **kwargs) -> requests.Response:
        return _request_with_retries(self.session.get, f"{self.base_url}{path}", **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return _request_with_retries(self.session.post, f"{self.base_url}{path}", **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return _request_with_retries(self.session.patch, f"{self.base_url}{path}", **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return _request_with_retries(self.session.delete, f"{self.base_url}{path}", **kwargs)


class GraphQLClient:
    """
    Sends GraphQL queries and mutations to the Strawberry /api/graphql endpoint.
    Raises AssertionError if the response contains top-level 'errors'.
    """

    def __init__(self, base_url: str, token: str | None = None):
        self.endpoint = f"{base_url.rstrip('/')}/api/graphql"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def query(self, query: str, variables: dict | None = None) -> dict:
        """
        Execute a GraphQL query or mutation.
        Returns the 'data' dict on success.
        Raises AssertionError if the response contains GraphQL errors.
        """
        payload = {"query": query, "variables": variables or {}}
        response = _request_with_retries(self.session.post, self.endpoint, json=payload)
        response.raise_for_status()
        body = response.json()
        assert "errors" not in body, (
            f"GraphQL errors in response: {body['errors']}"
        )
        return body.get("data", {})
