# utils/usecase_api.py
#
# Public GraphQL lookups for the consumer use case tests. Everything is one
# or two POSTs (aliased fields) rather than one per use case: the backend
# allows 1000 POST/hour per IP, and a per-use-case loop spent a seventh of
# that on every module that needed it.

import requests


def gql(api, query):
    r = requests.post(f"{api.rstrip('/')}/api/graphql", json={"query": query}, timeout=30)
    r.raise_for_status()
    body = r.json()
    assert not body.get("errors"), body["errors"]
    return body["data"]


def published_usecase_ids(api):
    rows = gql(api, "{ useCases(pagination:{limit:500}){ id status } }")["useCases"]
    return [u["id"] for u in rows if u["status"] == "PUBLISHED"]


def dashboards_by_usecase(api):
    """{use case id: [{id, name, link}]} for published use cases that have any dashboard."""
    ids = published_usecase_ids(api)
    fields = " ".join(f"u{i}: usecaseDashboards(usecaseId:{i}){{ id name link }}" for i in ids)
    data = gql(api, "{ " + fields + " }")
    return {i: data[f"u{i}"] for i in ids if data[f"u{i}"]}
