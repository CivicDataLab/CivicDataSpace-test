# tests/api/client.py
#
# Reusable HTTP clients for DataSpace REST and GraphQL API testing.

from __future__ import annotations

import requests


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
        return self.session.get(f"{self.base_url}{path}", **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.session.post(f"{self.base_url}{path}", **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.session.patch(f"{self.base_url}{path}", **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.session.delete(f"{self.base_url}{path}", **kwargs)


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
        response = self.session.post(self.endpoint, json=payload)
        response.raise_for_status()
        body = response.json()
        assert "errors" not in body, (
            f"GraphQL errors in response: {body['errors']}"
        )
        return body.get("data", {})
