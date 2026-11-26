# tests/api/smoke/test_api_065_sdg_search_filter.py
#
# Covers DataSpaceBackend#311 (open on dev since 2026-11-19, not yet merged):
# unified search gains an `sdgs` filter and facet, and the usecase/
# collaborative per-type search views accept the same `sdgs` filter, which
# matched nothing there before.
#
# Checked live on dev 2026-11-23 (pre-fix, before this PR):
#   - /api/search/unified/?types=usecase,collaborative : sdgs=SDG3 and
#     sdgs=NOTAREALSDG both return the full unfiltered total (395) -- the
#     parameter is silently ignored.
#   - /api/search/usecase/ and /api/search/collaborative/ : sdgs=SDG3 and
#     sdgs=NOTAREALSDG both return 0 -- the parameter matches nothing, for
#     any value, even one every record has.
#
# "How many should match" comes from the live useCasesTable/
# collaborativesTable GraphQL listing (`sdgs { code }`), not a hardcoded
# code or count -- SDG tagging is admin-managed data, like sectors (see
# SKILL.md: "Never hardcode admin-managed data"). On dev today SDG13 is on
# nearly every record (187/208 use cases, 182/187 collaboratives) and is
# useless for proving a filter narrows anything; the fixture below picks
# whichever code actually narrows both listings.
#
# Codes only, not names: two SDG names contain commas ("Industry,
# Innovation and Infrastructure" = SDG9, "Peace, Justice and Strong
# Institutions" = SDG16), and filter values are split on commas.
#
# pending_pr, not deployed_pr: GET-only, no writes, and per SKILL.md
# section 9 a pending test must never be `readonly` -- so a stale dev
# deploy here can never fail either DataSpace repo's prod gate.

import collections

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.pending_pr("DataSpaceBackend#311")]

_TABLES = {"usecase": "useCasesTable", "collaborative": "collaborativesTable"}


def _sdg_counts(anon_graphql_client, table):
    """{sdg code: number of published records carrying it}, from the live listing."""
    counts = collections.Counter()
    offset = 0
    total = None
    while True:
        body = anon_graphql_client.query(
            f"{{ {table}(includePublic: true, limit: 100, offset: {offset}) "
            "{ totalItemsCount data { id sdgs { code } } } }"
        )[table]
        total = body["totalItemsCount"]
        rows = body["data"]
        for row in rows:
            for sdg in row["sdgs"] or []:
                counts[sdg["code"]] += 1
        offset += len(rows)
        if len(rows) < 100 or offset >= total:
            break
    return counts, total


@pytest.fixture(scope="module")
def sdg_ground_truth(anon_graphql_client):
    """A single SDG code that narrows both usecase and collaborative search
    (0 < matches < total for each), picked from the live data."""
    per_kind = {kind: _sdg_counts(anon_graphql_client, table) for kind, table in _TABLES.items()}

    shared_codes = set(per_kind["usecase"][0]) & set(per_kind["collaborative"][0])
    for code in sorted(shared_codes):
        uc_count, uc_total = per_kind["usecase"][0][code], per_kind["usecase"][1]
        co_count, co_total = per_kind["collaborative"][0][code], per_kind["collaborative"][1]
        if 0 < uc_count < uc_total and 0 < co_count < co_total:
            return {
                "code": code,
                "usecase": uc_count,
                "collaborative": co_count,
                "unified": uc_count + co_count,
                "unified_total": uc_total + co_total,
            }
    pytest.skip("no single SDG code narrows both usecase and collaborative search on this environment")


def test_unified_search_filters_by_sdg_code(anon_api_client, sdg_ground_truth):
    """Unified search's total for one SDG code matches the live count for
    that code, not the unfiltered total (the pre-#311 bug: the parameter is
    ignored, so every value returns everything)."""
    gt = sdg_ground_truth
    resp = anon_api_client.get(
        "/api/search/unified/", params={"types": "usecase,collaborative", "sdgs": gt["code"], "page_size": 1}
    )
    assert resp.status_code == 200, f"unified search sdgs={gt['code']} failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    assert body["total"] == gt["unified"], (
        f"sdgs={gt['code']}: unified search returned {body['total']}, expected {gt['unified']} "
        f"(the unfiltered total is {gt['unified_total']} -- a total equal to that means the filter was ignored)"
    )


def test_unified_search_sdgs_filter_rejects_an_unknown_code(anon_api_client):
    """An SDG code nothing carries returns zero, not the unfiltered total."""
    resp = anon_api_client.get(
        "/api/search/unified/", params={"types": "usecase,collaborative", "sdgs": "SDGZZ", "page_size": 1}
    )
    assert resp.status_code == 200, f"unified search sdgs=SDGZZ failed ({resp.status_code}): {resp.text}"
    total = resp.json()["total"]
    assert total == 0, (
        f"sdgs=SDGZZ (no such code) matched {total} rows; "
        "a total equal to the unfiltered count means the filter was ignored, not applied"
    )


def test_unified_search_sdgs_filter_is_codes_not_names(anon_api_client):
    """A comma-bearing SDG *name* must not be split into fake codes and match anything."""
    resp = anon_api_client.get(
        "/api/search/unified/",
        params={"types": "usecase,collaborative", "sdgs": "Industry, Innovation and Infrastructure", "page_size": 1},
    )
    assert resp.status_code == 200, f"unified search failed ({resp.status_code}): {resp.text}"
    assert resp.json()["total"] == 0, "an SDG name (not a code) must match nothing"


def test_unified_search_exposes_an_sdgs_facet(anon_api_client):
    """The response carries an `sdgs` aggregation bucket, shaped like `sectors`."""
    resp = anon_api_client.get("/api/search/unified/", params={"types": "usecase,collaborative", "page_size": 1})
    assert resp.status_code == 200, f"unified search failed ({resp.status_code}): {resp.text}"
    aggs = resp.json()["aggregations"]
    assert "sdgs" in aggs, f"no 'sdgs' key in aggregations: {sorted(aggs)}"


@pytest.mark.parametrize("kind", ["usecase", "collaborative"])
def test_per_type_search_filters_by_sdg_code(anon_api_client, sdg_ground_truth, kind):
    """`/api/search/<kind>/?sdgs=<code>` matches exactly the live count for
    that code (the pre-#311 bug: it matched nothing, for any value)."""
    gt = sdg_ground_truth
    resp = anon_api_client.get(f"/api/search/{kind}/", params={"sdgs": gt["code"], "size": 1})
    assert resp.status_code == 200, f"{kind} search sdgs={gt['code']} failed ({resp.status_code}): {resp.text}"
    total = resp.json()["total"]
    assert total == gt[kind], f"{kind} search sdgs={gt['code']}: got {total}, expected {gt[kind]}"


@pytest.mark.parametrize("kind", ["usecase", "collaborative"])
def test_per_type_search_sdgs_filter_rejects_an_unknown_code(anon_api_client, kind):
    """Already true today (the filter currently matches nothing for any
    value) -- kept so a future change can't make an unknown code match."""
    resp = anon_api_client.get(f"/api/search/{kind}/", params={"sdgs": "SDGZZ", "size": 1})
    assert resp.status_code == 200, f"{kind} search failed ({resp.status_code}): {resp.text}"
    total = resp.json()["total"]
    assert total == 0, f"{kind} search sdgs=SDGZZ matched {total} rows, expected 0"
