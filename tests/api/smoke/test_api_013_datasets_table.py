# tests/api/smoke/test_api_013_datasets_table.py
#
# Covers the datasetsTable GraphQL query (DataSpaceBackend#215): a
# filterable, sortable, paginated view over datasets for a dashboard table,
# additive next to the existing `datasets` query.
#
# `readonly`: anonymous reads only, so it also runs in the prod gate.
# `deployed_pr` skips it wherever the backend doesn't serve #215 yet; on
# prod before the release the query doesn't exist ("Cannot query field
# 'datasetsTable'") and would fail every prod deploy instead.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#215")]


# ─── Visibility: unauthenticated + includePublic ───────────────────────────

@pytest.mark.smoke
def test_anon_include_public_returns_published_datasets_only(anon_graphql_client):
    """Not logged in + includePublic:true returns published datasets (only)."""
    data = anon_graphql_client.query(
        """
        query {
          datasetsTable(includePublic: true, limit: 5, offset: 0) {
            totalItemsCount
            statusCounts { status count }
            data { id title status resourceCount }
          }
        }
        """
    )
    table = data["datasetsTable"]
    assert table["totalItemsCount"] > 0, "expected at least one published dataset on dev"
    assert table["data"], "expected the first page to be non-empty"
    for row in table["data"]:
        assert row["status"] == "PUBLISHED", f"anon+includePublic leaked a non-public row: {row}"
    statuses = {row["status"] for row in table["statusCounts"]}
    assert statuses <= {"PUBLISHED"}, (
        f"anon+includePublic statusCounts should only ever show PUBLISHED, got: {statuses}"
    )


@pytest.mark.smoke
def test_anon_without_include_public_sees_nothing(anon_graphql_client):
    """Not logged in, includePublic omitted (defaults false): no rows at all.

    This is the privacy boundary the resolver's `_visible_datasets` enforces:
    an anonymous caller only gets datasets when it explicitly opts in to the
    public set. A regression here would mean the org/user-scoped case leaked
    to anonymous callers, or the default flipped to public.
    """
    data = anon_graphql_client.query(
        "{ datasetsTable(limit: 5, offset: 0) { totalItemsCount data { id } } }"
    )
    table = data["datasetsTable"]
    assert table["totalItemsCount"] == 0, table
    assert table["data"] == [], table


# ─── Filtering ──────────────────────────────────────────────────────────────

@pytest.mark.functional
def test_title_icontains_filter_narrows_results(anon_graphql_client):
    """An icontains title filter returns only matching rows, and fewer of them.

    The word is taken from live titles and must be missing from at least one,
    so a filter the resolver silently ignored could not pass.
    """
    page = anon_graphql_client.query(
        "{ datasetsTable(includePublic: true, limit: 50) { totalItemsCount data { title } } }"
    )["datasetsTable"]
    titles = [row["title"].lower() for row in page["data"]]
    word = next(
        (w for t in titles for w in t.split()
         if w.isalpha() and len(w) > 3 and any(w not in other for other in titles)),
        None,
    )
    if word is None:
        pytest.skip("no title word on dev that some datasets lack")

    filtered = anon_graphql_client.query(
        """
        query($word: String!) {
          datasetsTable(
            includePublic: true
            filters: [{field: "title", condition: "icontains", value: $word}]
            limit: 50
          ) { totalItemsCount data { title } }
        }
        """,
        {"word": word},
    )["datasetsTable"]
    assert 0 < filtered["totalItemsCount"] < page["totalItemsCount"], (
        f"filtering on {word!r} should narrow {page['totalItemsCount']} rows, "
        f"got {filtered['totalItemsCount']}"
    )
    for row in filtered["data"]:
        assert word in row["title"].lower(), f"row doesn't match the icontains filter: {row}"


@pytest.mark.functional
def test_filtering_on_an_unknown_field_is_a_graphql_error(anon_graphql_client):
    """A field outside the allowlist is rejected, naming the allowed fields.

    Guards api/utils/qs_utils.py's allowlist — the mechanism that keeps a
    table client from reaching arbitrary columns or relations.
    """
    payload = {
        "query": (
            '{ datasetsTable(includePublic: true, '
            'filters: [{field: "not_a_real_field", condition: "exact", value: "x"}]) '
            "{ totalItemsCount } }"
        )
    }
    response = anon_graphql_client.session.post(anon_graphql_client.endpoint, json=payload)
    response.raise_for_status()
    body = response.json()
    assert body.get("errors"), f"expected a GraphQL error, got: {body}"
    message = body["errors"][0]["message"]
    assert "not_a_real_field" in message, message
    assert "Allowed fields" in message, message


# ─── Shape: resourceCount and statusCounts ─────────────────────────────────

@pytest.mark.regression
def test_rows_carry_a_resource_count(anon_graphql_client):
    """Every row exposes the new `resourceCount` field as a non-negative int."""
    data = anon_graphql_client.query(
        "{ datasetsTable(includePublic: true, limit: 5) { data { id resourceCount } } }"
    )
    rows = data["datasetsTable"]["data"]
    if not rows:
        pytest.skip("no published datasets on dev")
    for row in rows:
        assert isinstance(row["resourceCount"], int), row
        assert row["resourceCount"] >= 0, row


@pytest.mark.regression
def test_status_counts_ignore_the_status_filter_itself(anon_graphql_client):
    """statusCounts is computed over every filter except `status`, so tab labels
    don't change when switching tabs.

    Filters on DRAFT: an anonymous caller only sees published datasets, so the
    rows come back empty while the counts must still show them. Filtering on
    PUBLISHED instead could not tell the two behaviours apart.
    """
    query = "{ datasetsTable(includePublic: true%s) { totalItemsCount statusCounts { status count } } }"
    unfiltered = anon_graphql_client.query(query % "")["datasetsTable"]
    if not unfiltered["statusCounts"]:
        pytest.skip("no published datasets on dev")
    drafts = anon_graphql_client.query(
        query % ', filters: [{field: "status", condition: "exact", value: "DRAFT"}]'
    )["datasetsTable"]
    assert drafts["totalItemsCount"] == 0, f"the status filter should still apply to rows: {drafts}"
    assert drafts["statusCounts"] == unfiltered["statusCounts"], (
        "adding a status filter must not change statusCounts "
        f"(unfiltered={unfiltered['statusCounts']}, filtered={drafts['statusCounts']})"
    )
