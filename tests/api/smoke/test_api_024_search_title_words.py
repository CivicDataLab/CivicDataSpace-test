# tests/api/smoke/test_api_024_search_title_words.py
#
# Covers DataSpaceBackend#235 (merge commit 26fe742e54adaaa9f45c3f63999685b450c0ad68):
# title-like fields (title/name/display_name) gained two ES sub-fields:
#
#   - `.words`  — whole-word, English-stemmed match. This is the only way a
#                 word SHORTER than 4 letters (e.g. "AI", "UN") can match a
#                 title at all: the main title field is a pure 4-letter
#                 n-gram (min_gram=max_gram=4), so a <4-letter query produces
#                 zero tokens against it, before or after #235.
#   - `.prefix` — search-as-you-type, word-start-anchored. A <4-letter
#                 PREFIX of a longer word (e.g. "Gem" for "Gemma") hits the
#                 same zero-token wall on the plain n-gram field, so it also
#                 could not match before #235.
#
# Both tests pick their target record from the live /api/search/aimodel/
# listing at runtime — never a hardcoded id or title — and require the match
# to genuinely narrow the result set (some, not all, not none), per the
# "flipping the expected value is not enough" lesson from CivicDataSpace-test#150.
#
# Read-only, anonymous GETs only. Marked `readonly` + `deployed_pr` because
# DataSpaceBackend#235 is on `dev` but not yet on `main`: the prod gate
# (run-smoke.yml's `readonly` suite) would otherwise fail against prod, which
# still serves the pre-#235 commit, until the feature ships. The marker skips
# these two tests wherever the target's /health/ git_sha doesn't yet contain
# #235's merge commit, and turns itself on automatically once it does.

import re

import pytest


def _has_word(text, word):
    """True if `word` appears in `text` as a whole word (case-insensitive)."""
    if not text:
        return False
    text = text.replace("&nbsp;", " ")
    return re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) is not None


@pytest.fixture(scope="module")
def aimodel_baseline(anon_api_client):
    """Unfiltered /api/search/aimodel/ listing, used as the 'total' baseline
    and as the pool to pick a title-only candidate word/prefix from."""
    resp = anon_api_client.get("/api/search/aimodel/", params={"size": 200})
    assert resp.status_code == 200, (
        f"baseline aimodel search failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    if not body.get("results"):
        pytest.skip("no AI model records on this environment to search over")
    return body


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#235")
def test_search_aimodel_short_word_matches_title_only(anon_api_client, aimodel_baseline):
    """
    A whole word under 4 letters that appears ONLY in an AI model's
    display_name (not its description, tags, or internal name) must be
    found by /api/search/aimodel/?query=<word>. Isolating it to the title
    rules out the match coming from description/tags fuzzy matching instead
    — the only field left that could have produced it is display_name.words.

    Confirmed live: on prod (still pre-#235 — DataSpaceBackend#235 has not
    reached `main`), the identical query against the identical record
    returns 0 hits. See PR body for the pasted red/green runs.
    """
    baseline_results = aimodel_baseline["results"]
    baseline_total = aimodel_baseline["total"]

    candidate = None
    for word in ("AI", "ML", "UN", "EV"):
        for r in baseline_results:
            dn = r.get("display_name") or ""
            if (
                _has_word(dn, word)
                and not _has_word(r.get("description"), word)
                and not _has_word(" ".join(r.get("tags") or []), word)
                and not _has_word(r.get("name"), word)
            ):
                candidate = r
                candidate_word = word
                break
        if candidate:
            break

    if not candidate:
        pytest.skip(
            "no AI model on this environment has a short whole word confined "
            "to its title field — data may have changed, nothing to test against"
        )

    resp = anon_api_client.get(
        "/api/search/aimodel/", params={"query": candidate_word, "size": 200}
    )
    assert resp.status_code == 200, f"search failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    filtered_total = body["total"]
    filtered_ids = {r["id"] for r in body["results"]}

    assert candidate["id"] in filtered_ids, (
        f"query={candidate_word!r} did not return aimodel id={candidate['id']} "
        f"({candidate['display_name']!r}), whose only field containing that word "
        f"is display_name — the display_name.words sub-field (#235) should match it"
    )
    # Must genuinely narrow the result set: some but not all/none records.
    # A `<=` here would pass even if the filter were silently ignored (#150).
    assert 0 < filtered_total < baseline_total, (
        f"query={candidate_word!r} returned {filtered_total} of {baseline_total} total — "
        f"expected a real subset, not everything or nothing"
    )


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#235")
def test_search_aimodel_short_prefix_matches_as_you_type(anon_api_client, aimodel_baseline):
    """
    A sub-4-letter PREFIX of a word in an AI model's display_name (e.g.
    "Gem" for "Gemma", picked at runtime, never hardcoded) must be found by
    /api/search/aimodel/?query=<prefix>. The old title field's 4-letter
    n-gram tokenizer produces no token for a 3-letter query either, so this
    is only reachable via the new display_name.prefix search-as-you-type
    sub-field (#235).

    Confirmed live: on prod (pre-#235) the identical query returns 0 hits.
    See PR body for the pasted red/green runs.
    """
    baseline_results = aimodel_baseline["results"]
    baseline_total = aimodel_baseline["total"]

    candidate = None
    prefix = None
    for r in baseline_results:
        dn = r.get("display_name") or ""
        for word in re.findall(r"[A-Za-z]{5,}", dn):
            prefix = word[:3]
            candidate = r
            break
        if candidate:
            break

    if not candidate:
        pytest.skip(
            "no AI model title on this environment has a word long enough to "
            "build a sub-4-letter prefix from"
        )

    resp = anon_api_client.get("/api/search/aimodel/", params={"query": prefix, "size": 200})
    assert resp.status_code == 200, f"search failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    filtered_total = body["total"]
    filtered_ids = {r["id"] for r in body["results"]}

    assert candidate["id"] in filtered_ids, (
        f"query={prefix!r} (prefix of a word in {candidate['display_name']!r}) did not "
        f"match id={candidate['id']} — the display_name.prefix sub-field (#235) should"
    )
    assert 0 < filtered_total < baseline_total, (
        f"query={prefix!r} returned {filtered_total} of {baseline_total} total — "
        f"expected a real subset, not everything or nothing"
    )
