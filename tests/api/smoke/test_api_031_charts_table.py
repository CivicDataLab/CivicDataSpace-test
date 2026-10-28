# tests/api/smoke/test_api_031_charts_table.py
#
# Covers the chartsTable GraphQL query (DataSpaceBackend#262): a filterable,
# sortable, paginated view over built charts and chart images, additive next
# to the existing `getChartData` query.
#
# `readonly`: anonymous-only, so it also runs in the prod gate. `deployed_pr`
# skips it wherever the backend doesn't serve #262 yet; on prod before the
# release the field doesn't exist at all ("Cannot query field 'chartsTable'")
# and would fail every prod deploy instead.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#262")]


@pytest.mark.smoke
def test_charts_table_field_exists(anon_graphql_client):
    """chartsTable is a field of Query -- the schema actually shipped the type.

    Guards against the field silently disappearing (a bad merge, a renamed
    resolver) without needing to be logged in to prove the shape landed.
    """
    data = anon_graphql_client.query('{ __type(name: "Query") { fields { name } } }')
    names = {f["name"] for f in data["__type"]["fields"]}
    assert "chartsTable" in names, names


@pytest.mark.regression
def test_anon_is_refused_like_get_chart_data(anon_graphql_client):
    """Not logged in: refused -- the same privacy rule getChartData enforces
    today (PR body: "Who sees what ... Same rules as getChartData ... Not
    logged in: refused"). Unlike datasetsTable, chartsTable has no
    includePublic opt-in: chart data is never public, so an anonymous caller
    must always be turned away by the permission class, never served an
    empty page.
    """
    payload = {
        "query": "{ chartsTable(limit: 5) { totalItemsCount data { __typename } } }"
    }
    response = anon_graphql_client.session.post(anon_graphql_client.endpoint, json=payload)
    response.raise_for_status()
    body = response.json()
    assert body.get("errors"), f"expected an anonymous caller to be refused, got: {body}"
    message = body["errors"][0]["message"]
    assert "permission" in message.lower(), message
    assert body.get("data") is None, body
