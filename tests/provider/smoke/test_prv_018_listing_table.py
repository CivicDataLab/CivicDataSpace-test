# tests/provider/smoke/test_prv_018_listing_table.py
#
# The listing table every provider dashboard section shares (DataSpaceFrontend#504):
# status tabs with counts, search, sort, pagination and the row Edit / Delete
# actions with their confirm dialog. Each section is checked for the individual
# account and for the account's organization.
#
# Records come from the API with a 'zz-auto-' name and are deleted by the
# `cleanup` fixture, so the tests never touch rows they did not create. Run the
# individual cases and the org cases with the account that owns them
# (TEST_USER_INDEX), e.g. `-k individual` / `-k org`.

import math
import uuid

import pytest

PAGE_SIZE = 10

# kind -> the sidebar section, the noun in the confirm dialog, and the API status
# behind the Draft / Published tabs.
LISTINGS = {
    "dataset": {"section": "Datasets", "noun": "dataset", "draft": "DRAFT", "published": "PUBLISHED"},
    "usecase": {"section": "Use Cases", "noun": "use case", "draft": "DRAFT", "published": "PUBLISHED"},
    "collaborative": {"section": "Collaboratives", "noun": "collaborative", "draft": "DRAFT", "published": "PUBLISHED"},
    "aimodel": {"section": "AI Models", "noun": "AI model", "draft": "REGISTERED", "published": "ACTIVE"},
}

scopes = pytest.mark.parametrize("scope", ["individual", "org"])
kinds = pytest.mark.parametrize("kind", list(LISTINGS))


def _owner(scope, request):
    """The org name a listing belongs to, or None for the individual's own records."""
    return request.getfixturevalue("writable_org") if scope == "org" else None


def _status_counts(listing):
    return {row["status"]: row["count"] for row in listing["statusCounts"]}


@pytest.mark.functional
@pytest.mark.smoke
@scopes
@kinds
def test_prv_018_listing_tabs_search_sort_and_delete(
    scope, kind, driver, open_listing, provider_api, cleanup, request
):
    """
    Test Case ID: test_prv_018_listing_tabs_search_sort_and_delete
    The All / Draft / Published tabs, search, sort and the row actions work on
    every provider listing.
    Steps:
      1. Create two drafts through the API
      2. Open the listing: the tab counts match the backend's counts
      3. Draft tab lists only drafts (including ours); Published lists none of ours
      4. Search narrows the table to our two drafts; a name that exists nowhere
         shows the empty state
      5. Sorting by name orders the two drafts the way the header says, and
         flips when clicked again
      6. Delete asks for confirmation: Cancel keeps the record, Delete removes it
      7. Edit on the remaining draft opens its editor
    """
    spec = LISTINGS[kind]
    org = _owner(scope, request)

    # 1. Two drafts with a shared, unique name stem.
    stem = f"zz-auto-lt-{uuid.uuid4().hex[:8]}"
    first, second = f"{stem}-a", f"{stem}-b"
    for title in (first, second):
        cleanup.track(kind, provider_api.create_draft(kind, title, org), org)
    backend = _status_counts(provider_api.listing(kind, org))
    draft_total = backend.get(spec["draft"], 0)
    published_total = backend.get(spec["published"], 0)

    # 2. Tab counts.
    table = open_listing(scope, spec["section"])
    table.wait_for_counts({"All": draft_total + published_total, "Draft": draft_total, "Published": published_total})

    # 3. Tabs filter by status.
    table.select_tab("Draft")
    rows = table.wait_for_rows(
        lambda r: len(r) == min(PAGE_SIZE, draft_total) and all(x["status"] == "Draft" for x in r),
        f"The Draft tab should list {min(PAGE_SIZE, draft_total)} draft rows, all with status Draft",
    )
    assert {first, second} <= {r["title"] for r in rows}, f"The Draft tab does not list our new drafts: {rows}"

    table.select_tab("Published")
    rows = table.wait_for_rows(
        lambda r: len(r) == min(PAGE_SIZE, published_total) and all(x["status"] == "Published" for x in r),
        f"The Published tab should list {min(PAGE_SIZE, published_total)} rows, all with status Published",
    )
    assert not {first, second} & {r["title"] for r in rows}, "The Published tab lists a draft"

    # 4. Search.
    table.select_tab("All").search(stem)
    rows = table.wait_for_rows(lambda r: len(r) == 2, f"Searching {stem!r} should leave our two drafts")
    assert {r["title"] for r in rows} == {first, second}

    table.search(f"{stem}-no-such-record")
    assert table.empty_message() == "No records match your filters"

    # 5. Sort. Searching again leaves just the two drafts; the name column starts unsorted.
    table.search(stem)
    table.wait_for_rows(lambda r: len(r) == 2, "Search did not narrow the table back to two rows")
    seen = []
    for _ in range(2):
        direction = table.sort_by_name().sort_direction()
        expected = sorted([first, second], reverse=direction == "descending")
        table.wait_for_rows(
            lambda r: [x["title"] for x in r] == expected,
            f"Sorted {direction}, the rows should read {expected}",
        )
        seen.append(direction)
    assert sorted(seen) == ["ascending", "descending"], f"Clicking the header twice sorted {seen}"

    # 6. Delete with confirmation.
    table.row_action(first, "Delete")
    dialog = table.dialog_text()
    assert f"Delete {spec['noun']}?" in dialog and first in dialog, f"Unexpected confirm dialog: {dialog!r}"
    table.answer_dialog("Cancel")
    assert first in provider_api.names(kind, org), "Cancel in the confirm dialog still deleted the record"
    assert first in table.titles()

    table.row_action(first, "Delete").answer_dialog("Delete")
    table.wait_for_rows(lambda r: [x["title"] for x in r] == [second], f"{first!r} is still listed after Delete")
    names = provider_api.names(kind, org)
    assert first not in names and second in names, "The backend still lists the deleted record, or lost the other one"

    # 7. Edit opens the draft in its editor.
    table.row_action(second, "Edit")
    assert "/edit" in driver.current_url


@pytest.mark.functional
@scopes
@kinds
def test_prv_019_listing_pagination(scope, kind, open_listing, provider_api, request):
    """
    Test Case ID: test_prv_019_listing_pagination
    A listing with more than one page of records pages correctly.
    Steps:
      1. Read the record count from the API; skip when it fits on one page
      2. Page 1 of N shows a full page, First/Previous disabled, Next/Last enabled
      3. Last Page shows the remainder and disables Next/Last
      4. First Page returns to the first rows
      5. Next Page shows a different set of rows; Previous Page returns
    """
    spec = LISTINGS[kind]
    org = _owner(scope, request)
    listing = provider_api.listing(kind, org)
    total = listing["totalItemsCount"]
    if total <= PAGE_SIZE:
        pytest.skip(f"Only {total} {spec['noun']} record(s) here: nothing to page through")
    pages = math.ceil(total / PAGE_SIZE)

    table = open_listing(scope, spec["section"])
    assert table.page() == (1, pages), (
        f"{total} records should make {pages} pages, saw {table.page()} (backend statusCounts: {listing['statusCounts']})"
    )
    first_page = table.wait_for_rows(lambda r: len(r) == PAGE_SIZE, "Page 1 is not a full page")
    assert not table.page_button_enabled("First Page") and not table.page_button_enabled("Previous Page")
    assert table.page_button_enabled("Next Page") and table.page_button_enabled("Last Page")

    table.go_to_page("Last Page")
    last_size = total - PAGE_SIZE * (pages - 1)
    table.wait_for_rows(lambda r: len(r) == last_size, f"The last page should list {last_size} rows")
    assert table.page() == (pages, pages)
    assert not table.page_button_enabled("Next Page") and not table.page_button_enabled("Last Page")
    assert table.page_button_enabled("Previous Page") and table.page_button_enabled("First Page")

    table.go_to_page("First Page")
    table.wait_for_rows(lambda r: r == first_page, "First Page did not return to the first rows")

    table.go_to_page("Next Page")
    table.wait_for_rows(lambda r: r != first_page, "Page 2 shows the same rows as page 1")
    assert table.page() == (2, pages)

    table.go_to_page("Previous Page")
    table.wait_for_rows(lambda r: r == first_page, "Previous Page did not return to the first rows")
