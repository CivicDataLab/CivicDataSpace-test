# tests/api/smoke/test_api_042_usecase_summary_search.py
#
# Covers DataSpaceBackend#277 ("don't index summary for now") and #278
# ("fix elastic search indexing"), merged back-to-back on 2026-11-04.
# #277 was a same-day mitigation that dropped "summary" from usecase search's
# searchable fields (an "immense term" Elasticsearch error on long rich-text
# summaries/descriptions was failing indexing entirely). #278 is the real
# fix: it removes the problem (a `raw` keyword-analyzed sub-field that tried
# to emit an oversized single token) from every long-text field across
# UseCase/Collaborative/AIModel/Publication/Publisher documents, and restores
# "summary" to usecase search.
#
# Net effect on dev right now: usecase search matches on summary content
# again. This test proves that positively, on live data.
#
# No true red/green via environment switching is available here: #277's
# broken window only existed on this same dev deployment for a few hours
# before #278 superseded it (both already merged by the time this test was
# written), and the feature predates `main`/prod entirely in its current
# form, so there is no reachable environment that reproduces #277's
# dropped-summary state to run this test against. The source PR itself
# directly unit-tests the fixed config (test_long_text_field_has_no_single_
# token_subfield, test_usecase_search_matches_on_summary in DataSpaceBackend).
# This test adds the black-box side: a real search query that only matches
# via summary content genuinely narrows live results, plus a negative
# control that an absent term matches nothing (so the narrowing isn't just
# "everything matches").

import pytest


@pytest.fixture(scope="module")
def usecase_baseline(anon_api_client):
    resp = anon_api_client.get("/api/search/usecase/", params={"size": 200})
    assert resp.status_code == 200, (
        f"baseline usecase search failed ({resp.status_code}): {resp.text}"
    )
    results = resp.json().get("results", [])
    if not results:
        pytest.skip("no usecase records on this environment to search over")
    return results


def _find_summary_only_word(results):
    """A word that appears in some usecase's `summary` but not in that
    usecase's own `title` — so a match for it can't be explained by title
    matching alone."""
    import re

    for uc in results:
        summary = uc.get("summary") or ""
        title = uc.get("title") or ""
        words = re.findall(r"[A-Za-z]{5,}", re.sub(r"<[^>]+>", " ", summary))
        title_lower = title.lower()
        for word in words:
            if word.lower() not in title_lower and len(word) >= 5:
                return word, uc
    return None, None


@pytest.mark.api
@pytest.mark.smoke
def test_usecase_search_matches_a_summary_only_word(anon_api_client, usecase_baseline):
    word, source_uc = _find_summary_only_word(usecase_baseline)
    if word is None:
        pytest.skip("no usecase summary on this environment has a distinctive word to search for")

    total = len(usecase_baseline)
    resp = anon_api_client.get("/api/search/usecase/", params={"query": word, "size": 200})
    assert resp.status_code == 200, f"search for {word!r} failed ({resp.status_code}): {resp.text}"
    filtered = resp.json().get("results", [])

    matched_ids = {uc["id"] for uc in filtered}
    assert source_uc["id"] in matched_ids, (
        f"searching for {word!r} (found only in usecase {source_uc['id']!r}'s "
        f"summary, not its title {source_uc['title']!r}) did not return that "
        "usecase — summary is not contributing to search matches"
    )
    # Genuinely narrows: neither vacuous (matches everything) nor a no-op.
    assert 0 < len(filtered) < total, (
        f"query {word!r} matched {len(filtered)}/{total} usecases — expected "
        "a proper subset, not everything or nothing"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_usecase_search_nonsense_term_matches_nothing(anon_api_client):
    """Sanity control: search isn't vacuously matching every record."""
    resp = anon_api_client.get(
        "/api/search/usecase/",
        params={"query": "zzzznonexistentsearchtermxyzzzqqq12345", "size": 10},
    )
    assert resp.status_code == 200, f"search failed ({resp.status_code}): {resp.text}"
    assert resp.json().get("results", []) == []
