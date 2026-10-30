# tests/api/smoke/test_api_029_listing_tables.py
#
# Covers DataSpaceBackend#254: four new GraphQL table queries for dashboard
# listings -- useCasesTable, collaborativesTable, aiModelsTable,
# publicationsTable -- built the same way as the existing `datasetsTable`
# (#215, see test_api_013_datasets_table.py), additive next to the existing
# useCases/collaboratives/aiModels/publications queries.
#
# `readonly`: every test here is an anonymous, unauthenticated GraphQL read.
# `deployed_pr`: #254 has not reached `main`/prod yet (confirmed via
# `git merge-base --is-ancestor <merge-sha> origin/main` in DataSpaceBackend),
# so this is gated the same way #215/#223/#245 were -- safe to merge into CI
# now, skips on prod until the release, turns on by itself after.
#
# Not covered here: publicationsTable. dev has zero published Publications
# right now ({ publications { id } } -> []), so there is nothing to assert a
# visibility or filtering invariant against -- see the skipped placeholder
# test at the bottom, which documents the gap instead of asserting on an
# empty, uninformative response.
#
# The second commit in #254 also refactors datasetsTable's status-counts
# logic into a shared `status_counts()` helper (api/utils/qs_utils.py) used by
# all five table queries now. test_api_013_datasets_table.py (unchanged) was
# re-run against dev as part of writing this and still passes -- the refactor
# didn't regress the existing query.

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#254")]


# ─── Visibility: anon + includePublic sees only the public set ────────────
#
# useCasesTable/collaborativesTable: anon's queryset is an exact
# `status=PUBLISHED` filter (api/schema/usecase_schema.py, collaborative_
# schema.py), so statusCounts for an anonymous caller must show PUBLISHED
# and nothing else. (aiModelsTable's public set is `is_public=True,
# is_active=True` -- a different pair of boolean flags, not the `status`
# enum -- so on live dev data it legitimately shows multiple statuses
# (ACTIVE and REGISTERED rows can both be "public and active"); that
# invariant does not hold for AI models and isn't asserted below.)

@pytest.mark.smoke
@pytest.mark.parametrize("query_name", ["useCasesTable", "collaborativesTable"])
def test_anon_include_public_sees_only_published_status(anon_graphql_client, query_name):
    data = anon_graphql_client.query(
        f"{{ {query_name}(includePublic: true, limit: 5) {{"
        f" totalItemsCount statusCounts {{ status count }} data {{ id }} }} }}"
    )[query_name]
    assert data["totalItemsCount"] > 0, f"expected at least one published row on dev ({query_name})"
    statuses = {row["status"] for row in data["statusCounts"]}
    assert statuses == {"PUBLISHED"}, (
        f"{query_name}: anon+includePublic statusCounts should only ever show "
        f"PUBLISHED, got {statuses} -- a regression here means the anon/public "
        "queryset started leaking non-published rows (or a status got excluded)."
    )


@pytest.mark.smoke
@pytest.mark.parametrize("query_name", ["useCasesTable", "collaborativesTable"])
def test_anon_without_include_public_still_sees_published_rows(anon_graphql_client, query_name):
    """Unlike datasetsTable, `includePublic` is a no-op for an anonymous
    caller here: `_visible_use_cases`/`_visible_collaboratives` already fall
    back to the PUBLISHED-only queryset for an unauthenticated, org-less
    caller whether or not `includePublic` is set (PR body says so explicitly:
    "This differs from datasetsTable, which returns nothing here"). Confirmed
    against live dev data (132/106 rows either way) before writing this --
    the naive "same as datasetsTable" assumption was wrong and would have
    asserted 0 here, which dev does not return.

    A regression that makes `includePublic` change this caller's result
    would mean the anon fallback branch is no longer always-PUBLISHED.
    """
    without = anon_graphql_client.query(
        f"{{ {query_name}(limit: 50) {{ totalItemsCount data {{ id status }} }} }}"
    )[query_name]
    with_flag = anon_graphql_client.query(
        f"{{ {query_name}(includePublic: true, limit: 50) {{ totalItemsCount data {{ id }} }} }}"
    )[query_name]
    assert without["totalItemsCount"] > 0, f"{query_name}: expected published rows on dev"
    assert without["totalItemsCount"] == with_flag["totalItemsCount"], (
        f"{query_name}: includePublic changed anon's result "
        f"({without['totalItemsCount']} vs {with_flag['totalItemsCount']}) -- "
        "the anon fallback branch should always be PUBLISHED-only regardless"
    )
    for row in without["data"]:
        assert row["status"] == "PUBLISHED", f"anon leaked a non-public row: {row}"


# ─── Filtering actually narrows the result (not silently ignored) ─────────

@pytest.mark.functional
def test_use_cases_table_title_filter_narrows_results(anon_graphql_client):
    page = anon_graphql_client.query(
        "{ useCasesTable(includePublic: true, limit: 50) { totalItemsCount data { title } } }"
    )["useCasesTable"]
    word = "testing"  # matched 1 of 132 live titles as of this PR
    filtered = anon_graphql_client.query(
        """
        query($word: String!) {
          useCasesTable(
            includePublic: true
            filters: [{field: "title", condition: "icontains", value: $word}]
            limit: 50
          ) { totalItemsCount data { title } }
        }
        """,
        {"word": word},
    )["useCasesTable"]
    assert 0 < filtered["totalItemsCount"] < page["totalItemsCount"], (
        f"filtering use_cases on {word!r} should narrow {page['totalItemsCount']} rows, "
        f"got {filtered['totalItemsCount']}"
    )
    for row in filtered["data"]:
        assert word in row["title"].lower(), f"row doesn't match the icontains filter: {row}"


@pytest.mark.functional
def test_collaboratives_table_title_filter_narrows_results(anon_graphql_client):
    page = anon_graphql_client.query(
        "{ collaborativesTable(includePublic: true, limit: 50) { totalItemsCount data { title } } }"
    )["collaborativesTable"]
    word = "test collab"  # matched 10 of 106 live titles as of this PR
    filtered = anon_graphql_client.query(
        """
        query($word: String!) {
          collaborativesTable(
            includePublic: true
            filters: [{field: "title", condition: "icontains", value: $word}]
            limit: 50
          ) { totalItemsCount data { title } }
        }
        """,
        {"word": word},
    )["collaborativesTable"]
    if filtered["totalItemsCount"] == 0:
        pytest.skip(f"no collaborativesTable title contains {word!r} on this environment any more")
    assert 0 < filtered["totalItemsCount"] < page["totalItemsCount"], (
        f"filtering collaboratives on {word!r} should narrow {page['totalItemsCount']} rows, "
        f"got {filtered['totalItemsCount']}"
    )


@pytest.mark.functional
def test_ai_models_table_filters_on_the_snake_case_field_name(anon_graphql_client):
    """`display_name` (the model's field name) works; the GraphQL-cased
    `displayName` is rejected by the same allowlist as datasetsTable's
    `not_a_real_field` case -- proving the allowlist is field-name-exact,
    not alias-tolerant, and that the valid name actually filters."""
    page = anon_graphql_client.query(
        "{ aiModelsTable(includePublic: true, limit: 50) { totalItemsCount } }"
    )["aiModelsTable"]

    filtered = anon_graphql_client.query(
        '{ aiModelsTable(includePublic: true, filters: ['
        '{field: "display_name", condition: "icontains", value: "New AI Model"}]) '
        "{ totalItemsCount } }"
    )["aiModelsTable"]
    assert 0 < filtered["totalItemsCount"] < page["totalItemsCount"], (
        f"display_name filter should narrow {page['totalItemsCount']} rows, "
        f"got {filtered['totalItemsCount']}"
    )

    response = anon_graphql_client.session.post(
        anon_graphql_client.endpoint,
        json={
            "query": (
                '{ aiModelsTable(includePublic: true, '
                'filters: [{field: "displayName", condition: "icontains", value: "x"}]) '
                "{ totalItemsCount } }"
            )
        },
    )
    response.raise_for_status()
    body = response.json()
    assert body.get("errors"), f"expected a GraphQL error for the camelCase field name, got: {body}"
    message = body["errors"][0]["message"]
    assert "displayName" in message and "Allowed fields" in message, message


# ─── statusCounts ignores the status filter itself (not vacuous) ──────────

@pytest.mark.regression
@pytest.mark.parametrize("query_name", ["useCasesTable", "collaborativesTable"])
def test_status_counts_ignore_the_status_filter_itself(anon_graphql_client, query_name):
    """Same shape as datasetsTable's equivalent test: filters on DRAFT, not
    PUBLISHED, because PUBLISHED is a no-op for an anon caller and could not
    tell "counts ignore the status filter" apart from "counts ignore every
    filter"."""
    query = f"{{ {query_name}(includePublic: true%s) {{ totalItemsCount statusCounts {{ status count }} }} }}"
    unfiltered = anon_graphql_client.query(query % "")[query_name]
    if not unfiltered["statusCounts"]:
        pytest.skip(f"no published rows on dev for {query_name}")
    drafts = anon_graphql_client.query(
        query % ', filters: [{field: "status", condition: "exact", value: "DRAFT"}]'
    )[query_name]
    assert drafts["totalItemsCount"] == 0, (
        f"{query_name}: the status filter should still apply to rows: {drafts}"
    )
    assert drafts["statusCounts"] == unfiltered["statusCounts"], (
        f"{query_name}: adding a status filter must not change statusCounts "
        f"(unfiltered={unfiltered['statusCounts']}, filtered={drafts['statusCounts']})"
    )


# ─── Gap: publicationsTable ────────────────────────────────────────────────

@pytest.mark.smoke
def test_publications_table_gap_no_published_rows_on_dev(anon_graphql_client):
    """Documents a real gap rather than asserting on an empty response.

    dev has zero published Publications right now, so there is no live data
    to check a visibility or filtering invariant against. This only checks
    the query itself doesn't error and shapes its (empty) response the same
    way as the others -- it is not a meaningful regression test for
    publicationsTable's actual filtering/visibility logic. Once a Publication
    is published on dev, extend this file with the same pattern used above
    for use cases/collaboratives.
    """
    data = anon_graphql_client.query(
        "{ publicationsTable(includePublic: true, limit: 5) {"
        " totalItemsCount statusCounts { status count } data { id } } }"
    )["publicationsTable"]
    if data["totalItemsCount"] > 0:
        pytest.skip("a Publication is now published on dev -- replace this with real coverage")
    assert data["data"] == [] and data["statusCounts"] == [], data


# ─── Authenticated visibility ──────────────────────────────────────────────
#
# Account 2 is the owner/member, account 3 the outsider (fixed, as in
# test_api_017, so the roles don't depend on which xdist worker runs this).
# Reads only. Records are picked at runtime; a missing case skips with why.

AUTH_TABLES = ["useCasesTable", "collaborativesTable", "aiModelsTable"]
ROW_BY_TABLE = {
    "useCasesTable": "id status organization { id } user { id }",
    "collaborativesTable": "id status organization { id } user { id }",
    "aiModelsTable": "id status isPublic isActive organization { id } user { id }",
}


def _rows(client, table, org=None, include_public=False, ids=None):
    """One page of `table` as `client` sees it; `ids` narrows to those rows."""
    args = "limit: 100"
    if include_public:
        args += ", includePublic: true"
    if ids is not None:
        args += ', filters: [{field: "id", condition: "in", value: "%s"}]' % ",".join(map(str, ids))
    body = pub.gql(
        client, "{ %s(%s) { totalItemsCount data { %s } } }" % (table, args, ROW_BY_TABLE[table]), org=org,
    )
    assert "errors" not in body, f"{table}: {body['errors']}"
    data = body["data"][table]
    assert data["totalItemsCount"] <= 100, f"{table}: more than one page ({data['totalItemsCount']}), narrow the query"
    return data["data"]


def _is_public(table, row):
    """The anonymous/includePublic set: PUBLISHED, or public+active for AI models."""
    if table == "aiModelsTable":
        return row["isPublic"] and row["isActive"]
    return row["status"] == "PUBLISHED"


def _org_id(row):
    return (row["organization"] or {}).get("id")


@pytest.fixture(scope="module")
def owner(graphql_client_for):
    return graphql_client_for(2)


@pytest.fixture(scope="module")
def outsider(graphql_client_for):
    return graphql_client_for(3)


@pytest.fixture(scope="module")
def owner_id(owner):
    return owner.query("{ me { id } }")["me"]["id"]


@pytest.mark.smoke
@pytest.mark.parametrize("table", AUTH_TABLES)
def test_signed_in_without_org_lists_only_own_rows(owner, owner_id, table):
    """No org header, no includePublic: the caller's own rows only (AI models:
    own rows with no organization). Broken scoping shows other users' rows."""
    rows = _rows(owner, table)
    if not rows:
        pytest.skip(f"account 2 owns no {table} rows on this environment")
    strangers = [r for r in rows if (r["user"] or {}).get("id") != owner_id]
    assert not strangers, f"{table}: rows owned by someone else: {strangers[:3]}"
    if table == "aiModelsTable":
        in_orgs = [r for r in rows if _org_id(r)]
        assert not in_orgs, f"aiModelsTable: own rows must have no organization: {in_orgs[:3]}"


@pytest.mark.smoke
@pytest.mark.parametrize("table", AUTH_TABLES)
def test_own_drafts_hidden_from_anonymous_and_outsider(owner, outsider, anon_graphql_client, table):
    hidden = {r["id"] for r in _rows(owner, table) if not _is_public(table, r)}
    if not hidden:
        pytest.skip(f"account 2 has no non-public {table} rows on this environment")
    for who, client in (("anonymous", anon_graphql_client), ("account 3", outsider)):
        seen = {r["id"] for r in _rows(client, table, include_public=True, ids=hidden)}
        assert not hidden & seen, f"{table}: {who} sees account 2's non-public rows {sorted(hidden & seen)[:5]}"


@pytest.fixture(scope="module")
def member_org_ids(owner):
    orgs = owner.query("{ userPermissions { organizations { organizationId } } }")["userPermissions"]["organizations"]
    if not orgs:
        pytest.skip("account 2 belongs to no organization")
    return [o["organizationId"] for o in orgs]


def _org_with_hidden_rows(owner, table, org_ids):
    """First member org whose table has a non-public row, with its rows."""
    for org in org_ids[:8]:  # ponytail: bounded scan to spare the 1000 POST/h budget
        rows = _rows(owner, table, org=org)
        if any(not _is_public(table, r) for r in rows):
            return org, rows
    pytest.skip(f"none of account 2's first 8 orgs has a non-public {table} row")


@pytest.mark.smoke
@pytest.mark.parametrize("table", AUTH_TABLES)
def test_org_header_lists_that_orgs_rows_including_drafts(owner, anon_graphql_client, member_org_ids, table):
    """With `organization: <id>` a member sees that org's rows -- only those,
    drafts included -- not their own-rows list and not just the public set."""
    org, rows = _org_with_hidden_rows(owner, table, member_org_ids)
    other_orgs = {_org_id(r) for r in rows} - {org}
    assert not other_orgs, f"{table}: org {org} listing has rows from {other_orgs}"
    drafts = {r["id"] for r in rows if not _is_public(table, r)}
    public = {r["id"] for r in _rows(anon_graphql_client, table, include_public=True, ids=drafts)}
    assert drafts - public, f"{table}: org {org} listing adds nothing beyond the public set"


@pytest.mark.smoke
@pytest.mark.xfail(strict=True, reason=(
    "DataSpaceBackend: the organization header is trusted without a membership "
    "check (_visible_use_cases & co., same as useCases/collaboratives/aiModels), "
    "so an anonymous caller lists any org's drafts. Verified on dev 2026-10-30."
))
@pytest.mark.parametrize("table", AUTH_TABLES)
def test_org_header_does_not_expose_drafts_to_anonymous(owner, anon_graphql_client, member_org_ids, table):
    org, rows = _org_with_hidden_rows(owner, table, member_org_ids)
    drafts = {r["id"] for r in rows if not _is_public(table, r)}
    seen = {r["id"] for r in _rows(anon_graphql_client, table, org=org)}
    assert not drafts & seen, f"{table}: anonymous + organization:{org} lists {len(drafts & seen)} non-public rows"
