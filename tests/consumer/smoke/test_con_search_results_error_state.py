# tests/consumer/smoke/test_con_search_results_error_state.py
#
# Pending coverage for DataSpaceFrontend#511 (head feat/s3-media-urls-v3,
# open on dev since 2026-10-29, not yet merged): a failed /search call must
# not leave the page stuck.
#
# Today, UnifiedListingComponent only captures the setter half of its error
# state ("const [, setError] = useState(...)"), so a failed fetchUnifiedData
# call sets an error nothing ever reads. The page is left on its "Loading"
# placeholder forever. #511 reads that state and renders "Unable to load
# results. Please try again later." instead.
#
# The trigger is a real, deterministic frontend bug, not a contrived
# backend error: `?types=dataset&page=abc` makes useUrlParams compute
# `currentPage = Number("abc")` = NaN, which is then sent to the backend as
# `...&page=NaN`, and `/api/search/unified/` 500s trying to int() that.
# Confirmed live on dev 2026-11-02 (see PR body for the exact console
# output): the console shows "Search error: Error: API returned 500:
# Internal Server Error" and the page never leaves "Loading".
#
# `pending_pr`: skipped until GitHub reports DataSpaceFrontend#511 merged.
# Never `readonly` -- see pr-test-sync SKILL.md §9 (the fix won't be on prod
# for a while after it merges to dev, and a pending `readonly` test would
# fail every prod deploy until then).
#
# No Page Object existed yet for /search (grepped locators/ and pages/ --
# this is the suite's first test of it), so this PR adds a minimal one
# (pages/consumer/search_page.py, locators/consumer/search_locators.py)
# scoped to exactly what this test needs, rather than a raw selector inline.

import os

import pytest

from pages.consumer.search_page import SearchPage

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.functional,
    pytest.mark.pending_pr("DataSpaceFrontend#511"),
]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

# types=dataset takes the search page off its sectioned "All" landing view,
# which otherwise ignores a bad page number and always requests page 1.
BROKEN_PAGE_QUERY = "types=dataset&page=abc"


def test_search_shows_an_error_message_instead_of_hanging(driver):
    """A failed search call must show the friendly error state, not hang.

    Before #511: times out here -- the page never leaves "Loading" because
    the error state that catch() sets is never read by the render.
    """
    page = SearchPage(driver).load(BASE_URL, BROKEN_PAGE_QUERY)
    shown = page.shows_unable_to_load_message(timeout=20)
    if not shown:
        page.save_failure_artifacts("con_search_error_state")
    assert shown, (
        f"{BASE_URL}/search?{BROKEN_PAGE_QUERY} never showed the "
        "'Unable to load results' message -- the page is likely stuck on "
        "its Loading placeholder instead (DataSpaceFrontend#511 not live)."
    )
