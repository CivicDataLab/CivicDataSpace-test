# tests/api/smoke/test_api_031_charts_table.py
#
# Covers the chartsTable GraphQL query (DataSpaceBackend#262): a filterable,
# sortable, paginated view over built charts and chart images, additive next
# to the existing `getChartData` query.
#
# `readonly`: reads only (anonymous, and the worker account's own charts),
# so it also runs in the prod gate. `deployed_pr` skips it wherever the backend doesn't serve #262 yet; on prod before the
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


# ─── Authenticated: the worker's account (graphql_client) ──────────────────

ROWS = """data { __typename
  ... on TypeResourceChart { id status chartType dataset { id } }
  ... on TypeResourceChartImage { id status dataset { id } } }"""


def _charts_table(client, args="", fields="totalItemsCount", org=None):
    """Raw chartsTable response body. `org` is sent as the `organization`
    header, which the backend middleware turns into the org context."""
    response = client.session.post(
        client.endpoint,
        json={"query": f"{{ chartsTable{args} {{ {fields} }} }}"},
        headers={"organization": org} if org else {},
    )
    response.raise_for_status()
    return response.json()


def _table(client, args="", fields="totalItemsCount", org=None):
    body = _charts_table(client, args, fields, org)
    assert not body.get("errors"), body["errors"]
    return body["data"]["chartsTable"]


@pytest.mark.smoke
def test_outsider_org_context_is_refused(graphql_client):
    """Logged in, but asking for an organisation's charts without being a
    member of it: refused by ChartDataPermission, not served that org's rows."""
    mine = {o["slug"] for o in graphql_client.query("{ organizations { slug } }")["organizations"]}
    others = [o["slug"] for o in graphql_client.query("{ allOrganizations { slug } }")["allOrganizations"]
              if o["slug"] not in mine]
    if not others:
        pytest.skip("this account is a member of every organisation")
    body = _charts_table(graphql_client, "(limit: 5)", "totalItemsCount", org=others[0])
    assert body.get("errors"), f"a non-member got {others[0]!r}'s charts: {body}"
    assert "permission" in body["errors"][0]["message"].lower(), body["errors"]


@pytest.mark.regression
@pytest.mark.parametrize("args, expected", [
    ("(limit: 0)", "limit (0) must be between 1 and 100"),
    ("(limit: 101)", "limit (101) must be between 1 and 100"),
    ("(offset: -1)", "offset (-1) must be 0 or more"),
    ('(filters: [{field: "not_a_real_field", value: "x"}])', "Cannot filter on 'not_a_real_field'. Allowed fields:"),
    ('(sortOptions: [{field: "not_a_real_field"}])', "Cannot sort on 'not_a_real_field'. Allowed fields:"),
], ids=["limit_0", "limit_101", "offset_negative", "filter_field", "sort_field"])
def test_invalid_page_filter_and_sort_input_is_rejected(graphql_client, args, expected):
    """qs_utils' bounds and allowlists apply to chartsTable. Runs in the
    account's own context, which an authenticated caller is always allowed."""
    body = _charts_table(graphql_client, args)
    assert body.get("errors"), f"expected {args} to be rejected, got: {body}"
    message = body["errors"][0]["message"]
    assert expected in message, message
    # Images are filtered first so the allowlist is named as clients know it,
    # not with the built-chart rewrite (resource__dataset…).
    assert "resource__" not in message, message
