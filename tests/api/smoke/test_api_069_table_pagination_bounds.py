# tests/api/smoke/test_api_069_table_pagination_bounds.py
#
# Every dashboard listing query takes limit and offset from the caller, so each
# must refuse values outside its range with a readable error (never a 5xx or a
# partial page), serve a page at the largest allowed limit, and answer an offset
# past the end with an empty page. Read-only queries, one small query per case.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke]

TABLES = ["datasetsTable", "useCasesTable", "collaborativesTable", "aiModelsTable", "publicationsTable", "chartsTable", "eventsTable"]


def _table(client, name, args):
    body = client.session.post(client.endpoint, json={"query": "{ %s(%s){ totalItemsCount data { __typename } } }" % (name, args)}, timeout=60)
    assert body.status_code == 200, f"{name}({args}) answered HTTP {body.status_code}"
    return body.json()


@pytest.fixture(scope="module")
def client(graphql_client_for):
    return graphql_client_for(1)


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.parametrize("args, message", [
    ("limit: 0", "between 1 and 100"),
    ("limit: -1", "between 1 and 100"),
    ("limit: 101", "between 1 and 100"),
    ("limit: 10, offset: -5", "0 or more"),
    ("limit: 10, offset: 99999999999", "32-bit"),
], ids=["limit-0", "limit-negative", "limit-101", "offset-negative", "offset-over-32-bits"])
def test_out_of_range_paging_is_a_readable_error(client, table, args, message):
    body = _table(client, table, args)
    assert body.get("errors"), f"{table}({args}) was accepted: {str(body)[:200]}"
    assert any(message in e["message"] for e in body["errors"]), f"{table}({args}) said {body['errors'][0]['message']!r}"
    assert not (body.get("data") or {}).get(table), f"{table}({args}) returned rows along with the error"


@pytest.mark.parametrize("table", TABLES)
def test_largest_page_and_an_offset_past_the_end(client, table):
    full = _table(client, table, "limit: 100")
    assert not full.get("errors"), f"{table}(limit: 100) failed: {full['errors']}"
    total = full["data"][table]["totalItemsCount"]
    assert len(full["data"][table]["data"]) == min(100, total), f"{table} returned a short or long page for limit 100"

    past = _table(client, table, f"limit: 10, offset: {total + 1000}")
    assert not past.get("errors"), f"{table} refused an offset past the end: {past['errors']}"
    assert past["data"][table]["data"] == [], f"{table} returned rows past the end"
