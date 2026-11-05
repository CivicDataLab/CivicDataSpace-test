# tests/api/smoke/test_api_026_usecase_summary_search.py
#
# Covers whether a usecase's `summary` is actually searchable
# (DataSpaceBackend#277 "don't index summary for now", #278 "fix elastic
# search indexing", #281 "fix(search): rebuild indexes that still have
# single-token long text copies").
#
# The three merged within 20 minutes of each other on 2026-11-04 and are
# one continuous incident: #277 dropped `summary` from the searchable
# fields as a stopgap for an Elasticsearch "immense term" indexing error
# (long summaries have a `raw` keyword sub-field that can't hold a token
# over Lucene's 32,766-byte limit); #278 fixed the mapping and put
# `summary` back; #281 adds a migration to rebuild indexes created under
# the old, broken mapping. All three are covered together here.
#
# DataSpaceBackend's own test suite (tests/test_search_long_text_mapping.py,
# tests/test_rebuild_long_text_indexes.py, added in #278/#281) already
# covers the ES document mapping and the migration's rebuild logic at the
# unit level, with mocks. This file complements that with the one thing
# those unit tests can't show: that a real summary, on the live dev index,
# is actually matched by search today.
#
# Not marked `readonly`: not needed either way here (this only reads
# public search results), but there's nothing prod-specific being proven.

import re

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke]

TAG_RE = re.compile(r"<[^>]+>")
WORD_RE = re.compile(r"[A-Za-z]{5,}")

# Generic enough to show up in almost any usecase summary — excluded so a
# distinctive candidate word doesn't accidentally match on these instead.
COMMON_WORDS = {
    "about", "which", "where", "there", "these", "those", "would", "could",
    "should", "their", "other", "being", "doing", "having", "between",
    "through", "during", "under", "while", "study", "studies", "analysis",
    "analyses", "ensure", "across", "within", "level", "levels", "india",
}


def _distinctive_summary_word(title: str, tags: list, summary_html: str):
    """A word that appears in `summary_html` but not in `title` or `tags`."""
    text = TAG_RE.sub(" ", summary_html or "")
    other_text = f"{title} {' '.join(tags or [])}".lower()
    for word in WORD_RE.findall(text):
        lowered = word.lower()
        if lowered in COMMON_WORDS or lowered in other_text:
            continue
        return word
    return None


@pytest.fixture(scope="module")
def summary_only_search_case(anon_api_client):
    """A real (title, distinctive summary word) pair, read live from dev.

    Checks a few pages of published usecases for one whose summary has a
    word that isn't also in its own title or tags, so a search on that word
    can only be explained by the summary being indexed.
    """
    for page in (1, 2, 3):
        resp = anon_api_client.session.get(
            f"{anon_api_client.base_url}/api/search/usecase/",
            params={"page": page, "size": 20},
            timeout=30,
        )
        assert resp.status_code == 200, (
            f"GET /api/search/usecase/?page={page} failed ({resp.status_code}): "
            f"{resp.text[:300]}"
        )
        results = resp.json().get("results", [])
        if not results:
            break
        for case in results:
            word = _distinctive_summary_word(
                case.get("title", ""), case.get("tags", []), case.get("summary", "")
            )
            if word:
                return {"title": case["title"], "word": word}
    pytest.skip(
        "No published usecase on dev has a summary word distinct from its "
        "own title/tags — nothing to probe search with"
    )


def test_usecase_search_matches_on_summary_text(
    anon_api_client, summary_only_search_case
):
    """Searching a word that only appears in the summary must find that usecase.

    This is exactly the behaviour #277 broke (summary excluded from
    searchable_fields) and #278 restored.
    """
    word = summary_only_search_case["word"]
    resp = anon_api_client.session.get(
        f"{anon_api_client.base_url}/api/search/usecase/",
        params={"page": 1, "size": 20, "query": word},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /api/search/usecase/?query={word} failed ({resp.status_code}): "
        f"{resp.text[:300]}"
    )
    titles = [r.get("title") for r in resp.json().get("results", [])]
    assert summary_only_search_case["title"] in titles, (
        f"Searching for {word!r} (found only in this usecase's summary) did "
        f"not return {summary_only_search_case['title']!r}. Got: {titles}"
    )
