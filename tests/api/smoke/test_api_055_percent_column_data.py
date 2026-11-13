# tests/api/smoke/test_api_055_percent_column_data.py
"""The data API reads tables whose column names contain a percent sign.

DataSpaceBackend#295: psycopg2 %-formats the whole query text, so a quoted
header like "IMR (%)" broke every read, select, filter and sort on the table
with 500 {"error": "Failed to fetch data"}. Indicator tables use such headers
all the time.
"""

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#295")]

QUERY = "{ datasets(includePublic: true, pagination: {limit: 200, offset: %d}) { status resources { id schema { fieldName } } } }"


@pytest.fixture(scope="module")
def percent_resource(anon_graphql_client, anon_api_client):
    """(resource id, '%' column) for a published, indexed table."""
    for offset in range(0, 2000, 200):
        rows = anon_graphql_client.query(QUERY % offset)["datasets"]
        for d in rows:
            if d["status"] != "PUBLISHED":
                continue
            for r in d["resources"]:
                col = next((f["fieldName"] for f in r.get("schema") or [] if "%" in (f["fieldName"] or "")), None)
                # 404 = not indexed (not a table); anything else reaches the query.
                if col and anon_api_client.get(f"/api/resources/{r['id']}/data/", params={"limit": 1, "count": "false"}).status_code != 404:
                    return r["id"], col
        if len(rows) < 200:
            break
    pytest.skip("no published, indexed table with a '%' column on this backend")


def read(anon_api_client, percent_resource, **params):
    resource_id, _ = percent_resource
    resp = anon_api_client.get(f"/api/resources/{resource_id}/data/", params={"limit": 5, **params})
    assert resp.status_code == 200, f"{params or 'plain read'} returned {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert body["rows"], f"{params or 'plain read'} returned no rows"
    return body


@pytest.mark.smoke
@pytest.mark.regression
def test_plain_read_of_a_table_with_a_percent_column(anon_api_client, percent_resource):
    body = read(anon_api_client, percent_resource)
    assert percent_resource[1] in body["columns"]


@pytest.mark.smoke
@pytest.mark.regression
def test_select_and_sort_on_a_percent_column(anon_api_client, percent_resource):
    col = percent_resource[1]
    body = read(anon_api_client, percent_resource, columns=col, order_by=f"-{col}")
    assert body["columns"] == [col]


@pytest.mark.smoke
@pytest.mark.regression
def test_filter_on_a_percent_column(anon_api_client, percent_resource):
    col = percent_resource[1]
    first = read(anon_api_client, percent_resource, columns=col)["rows"][0][0]
    body = read(anon_api_client, percent_resource, columns=col, **{col: first})
    assert all(row[0] == first for row in body["rows"]), f"filter {col}={first!r} returned {body['rows']}"
