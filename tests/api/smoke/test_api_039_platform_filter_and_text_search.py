# tests/api/smoke/test_api_039_platform_filter_and_text_search.py
#
# Covers the parts of two DataSpaceBackend PRs that nothing on CI exercised.
#
# #204 (platform import, merge 40cf8c2). test_api_020 only checks that the
# `source_platform` aggregation key exists. Not covered until here:
#   - the `source_platform` request filter on /api/search/dataset/ (a single
#     platform, a comma list, and "NATIVE" = datasets that were not imported);
#   - an imported dataset's EXTERNAL resource exposing `url` (new field on
#     TypeResource) and pointing at the same page as `source.sourceUrl`.
#
# #231 (analysed listing search, merge 859fe6c). The per-type search views swapped
# a term-level `fuzzy` query (case-sensitive, text not split) for api/utils/
# search_query.text_query. test_api_021 covers one publication title word and
# test_api_024 covers #235's sub-4-letter words on aimodel only. Not covered:
# the other listing types, upper-case text, and multi-word text where every
# token is required (the old query matched on any token).
#
# Targets are picked from the live listing at runtime. Read-only, anonymous.
# `readonly` + `deployed_pr` so the prod gate skips them until prod serves the PR.

import re

import pytest

LISTINGS = {  # search type -> title field
    "dataset": "title",
    "usecase": "title",
    "collaborative": "title",
    "aimodel": "display_name",
}


def _search(client, kind, **params):
    resp = client.get(f"/api/search/{kind}/", params={"size": 100, **params})
    assert resp.status_code == 200, f"{kind} search {params} failed ({resp.status_code}): {resp.text}"
    return resp.json()


# ---------------------------------------------------------------- #204


@pytest.fixture(scope="module")
def dataset_baseline(anon_api_client):
    return _search(anon_api_client, "dataset")


@pytest.fixture(scope="module")
def imported_counts(dataset_baseline):
    """{platform: doc_count} for datasets that were imported, from the live aggregation."""
    buckets = dataset_baseline["aggregations"]["source_platform"]["buckets"]
    counts = {b["key"]: b["doc_count"] for b in buckets}
    if not counts:
        pytest.skip("no imported datasets on this environment to filter by")
    return counts


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#204")
@pytest.mark.parametrize("case", ["one_platform", "platform_list", "native"])
def test_dataset_search_source_platform_filter(anon_api_client, dataset_baseline, imported_counts, case):
    """`source_platform` narrows dataset search to exactly the matching datasets."""
    total = dataset_baseline["total"]
    platforms = sorted(imported_counts)
    if case == "one_platform":
        value, expected = platforms[0], imported_counts[platforms[0]]
    elif case == "platform_list":
        # A comma list is split into a terms filter; the extra value matches nothing.
        value, expected = ",".join([*platforms, "NO_SUCH_PLATFORM"]), sum(imported_counts.values())
    else:
        value, expected = "NATIVE", total - sum(imported_counts.values())

    body = _search(anon_api_client, "dataset", source_platform=value)
    assert body["total"] == expected, f"source_platform={value!r}: {body['total']} of {total}, expected {expected}"
    assert body["total"] < total, "the filter did not narrow the result set"
    for row in body["results"]:
        if case == "native":
            assert row.get("source_platform") is None, f"imported dataset in NATIVE results: {row['id']}"
        else:
            assert row.get("source_platform") in platforms, f"{row['id']} has source_platform={row.get('source_platform')!r}"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#204")
def test_imported_dataset_resource_url_matches_source(anon_graphql_client):
    """A link-only import has an EXTERNAL resource whose `url` is the platform page."""
    rows = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 100}) "
        "{ id source { sourceUrl } resources { type url } } }"
    )["datasets"]
    imported = [r for r in rows if r["source"]]
    if not imported:
        pytest.skip("no imported dataset among the first 100 public datasets")
    for row in imported:
        urls = [res["url"] for res in row["resources"] if res["type"] == "EXTERNAL"]
        assert row["source"]["sourceUrl"] in urls, (
            f"dataset {row['id']}: no EXTERNAL resource linking to {row['source']['sourceUrl']}, got {urls}"
        )


# ---------------------------------------------------------------- #231


@pytest.fixture(scope="module", params=sorted(LISTINGS))
def listing(request, anon_api_client):
    """(search type, a record whose title has 2+ words of 5+ letters, its words, baseline total)."""
    kind = request.param
    body = _search(anon_api_client, kind)
    for rec in body["results"]:
        title = rec.get(LISTINGS[kind]) or ""
        words = re.findall(r"[A-Za-z]{5,}", title)
        if len(words) >= 2:
            return kind, rec, words, body["total"]
    pytest.skip(f"no {kind} title with two 5+ letter words on this environment")


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#231")
def test_search_matches_title_regardless_of_case(anon_api_client, listing):
    """The search text is analysed like the stored text: the title in capitals still finds it."""
    kind, rec, _, total = listing
    title = rec[LISTINGS[kind]]
    body = _search(anon_api_client, kind, query=title.upper())
    assert rec["id"] in {r["id"] for r in body["results"]}, f"{kind}: {title.upper()!r} did not find {title!r}"
    assert body["total"] < total, f"{kind}: query returned {body['total']} of {total}"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#231")
def test_search_multiword_text_requires_every_word(anon_api_client, listing):
    """Two title words find that record and narrow the list (any-word matching returned far more)."""
    kind, rec, words, total = listing
    body = _search(anon_api_client, kind, query=" ".join(words[:2]))
    assert rec["id"] in {r["id"] for r in body["results"]}, f"{kind}: {words[:2]} did not find {rec[LISTINGS[kind]]!r}"
    assert 0 < body["total"] < total, f"{kind}: query returned {body['total']} of {total}"
