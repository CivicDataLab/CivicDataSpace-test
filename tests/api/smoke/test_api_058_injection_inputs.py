# tests/api/smoke/test_api_058_injection_inputs.py
#
# Text typed into a public search or filter box is data, never code. Each
# payload (SQL, query-language and template metacharacters, script tags, path
# traversal, a very long string) goes into the listing filters and the search
# endpoints as an anonymous caller. Expected: the API answers normally, every
# row it returns really contains the payload text (so it was matched literally,
# not interpreted), and no response shows a database error, stack trace or
# file path. Anonymous and read-only.

import re

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.smoke, pytest.mark.readonly]

PAYLOADS = [
    "'",
    '"',
    "\\",
    "' OR '1'='1",
    "'; DROP TABLE api_dataset;--",
    "1 UNION SELECT NULL--",
    "%' OR 1=1 --",
    "<script>alert(1)</script>",
    "${7*7}",
    "{{7*7}}",
    "../../etc/passwd",
    '") { id } } query { me { id } } #',
    "a" * 5000,
]
TABLES = ["datasetsTable", "useCasesTable", "collaborativesTable"]
SEARCH = ["/api/search/dataset/", "/api/search/usecase/"]
LEAK = re.compile(
    r"Traceback|psycopg|django\.|\bSELECT\b|syntax error|/app/|\.py\"|elasticsearch|ProgrammingError|OperationalError",
    re.I,
)


def _post(api_base_url, query, variables):
    return requests.post(f"{api_base_url}/api/graphql", json={"query": query, "variables": variables}, timeout=60)


def _filter(api_base_url, table, payload):
    query = ("query($f:[FilterSpec!]){ %s(includePublic:true, limit:20, filters:$f){ totalItemsCount data{ id title } } }"
             % table)
    variables = {"f": [{"field": "title", "condition": "icontains", "value": payload}]}
    return _post(api_base_url, query, variables)


@pytest.mark.parametrize("payload", PAYLOADS, ids=lambda p: p[:20])
@pytest.mark.parametrize("table", TABLES)
def test_title_filter_treats_the_payload_as_text(api_base_url, table, payload):
    resp = _filter(api_base_url, table, payload)
    assert resp.status_code == 200, f"{table} answered {resp.status_code} for {payload[:30]!r}: {resp.text[:200]}"
    assert not LEAK.search(resp.text), f"{table} leaked internals for {payload[:30]!r}: {resp.text[:300]}"
    body = resp.json()
    assert "errors" not in body, f"{table} errored for {payload[:30]!r}: {body['errors'][0]['message'][:200]}"
    for row in body["data"][table]["data"]:
        assert payload.lower() in (row["title"] or "").lower(), (
            f"{table} returned {row['title']!r} for the filter {payload[:30]!r}, which it does not contain: "
            "the value was not matched as plain text")


def test_nul_character_is_refused_without_internals(api_base_url):
    resp = _filter(api_base_url, "datasetsTable", "a\x00b")
    assert resp.status_code < 500, f"NUL in a filter value gave {resp.status_code}: {resp.text[:200]}"
    assert not LEAK.search(resp.text), f"NUL in a filter value leaked internals: {resp.text[:300]}"


@pytest.mark.parametrize("payload", PAYLOADS[:12], ids=lambda p: p[:20])
@pytest.mark.parametrize("path", SEARCH)
def test_search_endpoint_treats_the_payload_as_text(api_base_url, path, payload):
    resp = requests.get(f"{api_base_url}{path}", params={"query": payload, "size": 5}, timeout=60)
    assert resp.status_code == 200, f"{path} answered {resp.status_code} for {payload[:30]!r}: {resp.text[:200]}"
    assert resp.headers.get("content-type", "").startswith("application/json"), (
        f"{path} answered {resp.headers.get('content-type')!r} for {payload[:30]!r}")
    assert not LEAK.search(resp.text), f"{path} leaked internals for {payload[:30]!r}: {resp.text[:300]}"
