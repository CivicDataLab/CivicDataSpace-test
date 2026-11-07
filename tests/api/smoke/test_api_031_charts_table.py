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


@pytest.fixture(scope="module")
def charts(graphql_client):
    """(org, table) for the first context of this account that lists charts:
    its own (no org), then each organisation it belongs to."""
    orgs = [o["slug"] for o in graphql_client.query("{ organizations { slug } }")["organizations"]]
    for org in [None, *orgs]:
        table = _table(graphql_client, "(limit: 100)", f"totalItemsCount statusCounts {{ status count }} {ROWS}", org)
        if table["totalItemsCount"]:
            return org, table
    pytest.skip(f"this account has no charts or chart images in its own context or in {orgs}")


def _kind(row):
    return {"TypeResourceChart": "CHART", "TypeResourceChartImage": "IMAGE"}[row["__typename"]]


@pytest.mark.functional
def test_kind_filter_splits_rows_into_their_own_types(graphql_client, charts):
    """kind=CHART and kind=IMAGE partition the table, and the UNION merge
    resolves each row to its own type: a CHART row is a TypeResourceChart, an
    IMAGE row a TypeResourceChartImage. Asked per kind rather than picked from
    the page, so images rendered as built charts fail instead of skipping."""
    org, table = charts
    assert len(table["data"]) == min(table["totalItemsCount"], 100), "rows were dropped while merging the two tables"
    totals = {}
    for kind in ("CHART", "IMAGE"):
        filtered = _table(
            graphql_client, f'(limit: 100, filters: [{{field: "kind", value: "{kind}"}}])', f"totalItemsCount {ROWS}", org
        )
        totals[kind] = filtered["totalItemsCount"]
        for row in filtered["data"]:
            assert _kind(row) == kind, f"kind={kind} returned a {row['__typename']}: {row}"
    assert sum(totals.values()) == table["totalItemsCount"], f"kinds {totals} don't add up to {table['totalItemsCount']}"
    if not all(totals.values()):
        pytest.skip(f"this account's charts are all one kind ({totals}); the merge needs both")


@pytest.mark.functional
@pytest.mark.parametrize("field, key", [
    ("chart_type", lambda row: row.get("chartType")),
    ("dataset", lambda row: (row.get("dataset") or {}).get("id")),
], ids=["chart_type", "dataset"])
def test_filter_narrows_to_matching_rows(graphql_client, charts, field, key):
    """Each filter returns only matching rows, and fewer of them. The value is
    picked from live rows and some visible row must lack it, so a filter the
    resolver ignored could not pass."""
    org, table = charts
    rows = table["data"]
    values = [key(r) for r in rows]
    candidates = [v for v in values if v is not None and any(x != v for x in values)]
    if not candidates:
        pytest.skip(f"no {field} value that only some of this account's charts have")
    value = max(set(candidates), key=lambda v: (values.count(v), str(v)))

    filtered = _table(
        graphql_client,
        f'(limit: 100, filters: [{{field: "{field}", value: "{value}"}}])',
        f"totalItemsCount {ROWS}",
        org,
    )
    assert 0 < filtered["totalItemsCount"] < table["totalItemsCount"], (
        f"filtering {field}={value!r} should narrow {table['totalItemsCount']} rows, "
        f"got {filtered['totalItemsCount']}"
    )
    for row in filtered["data"]:
        assert key(row) == value, f"row doesn't match {field}={value!r}: {row}"


@pytest.mark.functional
def test_status_counts_ignore_the_status_filter_itself(graphql_client, charts):
    """statusCounts is computed over every filter except `status`, summed
    over both tables. The status picked is one the filter actually changes the
    rows for (a minority status, else one no chart has), so counts computed
    with the status filter applied could not pass."""
    org, table = charts
    counts = {c["status"]: c["count"] for c in table["statusCounts"]}
    total = table["totalItemsCount"]
    assert sum(counts.values()) == total, f"statusCounts {counts} don't add up to {total}"
    status = min(("DRAFT", "PUBLISHED", "ARCHIVED"), key=lambda s: (counts.get(s, 0) == total, counts.get(s, 0)))

    filtered = _table(
        graphql_client,
        f'(filters: [{{field: "status", value: "{status}"}}])',
        "totalItemsCount statusCounts { status count }",
        org,
    )
    assert filtered["totalItemsCount"] == counts.get(status, 0) != total, (
        f"the status filter should still apply to rows: {status} -> {filtered}"
    )
    assert filtered["statusCounts"] == table["statusCounts"], (
        "adding a status filter must not change statusCounts "
        f"(unfiltered={table['statusCounts']}, filtered={filtered['statusCounts']})"
    )
