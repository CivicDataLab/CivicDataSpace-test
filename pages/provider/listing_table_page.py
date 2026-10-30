# pages/provider/listing_table_page.py

import re

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from locators.provider.listing_table_locators import ListingTableLocators as L
from pages.base_page import BasePage


class ListingTablePage(BasePage):
    """The listing table every provider dashboard section shares (see L).

    Actions only; the tests assert. Waits are on the state a step should produce,
    since the table keeps showing the previous rows while a new query is running.
    """

    def open_section(self, section: str) -> "ListingTablePage":
        """Open a section from the dashboard sidebar and wait for its counts to load."""
        link = self.wait_with_timeout(20).until(
            EC.presence_of_element_located((By.XPATH, L.SIDEBAR_LINK.format(section=section))),
            message=f"No '{section}' link in the dashboard sidebar",
        )
        self.driver.execute_script("arguments[0].click();", link)
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located((By.XPATH, L.HEADING.format(section=section))),
            message=f"The '{section}' listing never opened",
        )
        self.status_counts()
        return self

    # ─── Status tabs ─────────────────────────────────────────────────────────

    def status_counts(self) -> dict[str, int]:
        """{'All': n, 'Draft': n, 'Published': n}, once the counts have loaded."""
        def read(d):
            counts = {}
            for tab in d.find_elements(*L.TABS):
                match = re.fullmatch(r"(\w+)\s+(\d+)", tab.text.strip())
                if match:
                    counts[match.group(1)] = int(match.group(2))
            return counts if len(counts) == 3 else False

        return self.wait_with_timeout(30).until(read, message="The status tabs never showed their counts")

    def wait_for_counts(self, expected: dict[str, int]) -> dict[str, int]:
        """Wait for the tabs to show `expected`; fail with what they did show.

        The tabs read 0 / 0 / 0 until the first query settles, so a count can only
        be judged against a value known in advance.
        """
        last = {}

        def matches(d):
            nonlocal last
            last = self.status_counts()
            return last == expected

        try:
            return self.wait_with_timeout(30).until(matches)
        except TimeoutException:
            raise AssertionError(f"The tabs show {last}, the backend says {expected}") from None

    def select_tab(self, label: str) -> "ListingTablePage":
        tab = (By.XPATH, L.TAB.format(label=label))
        self.click_until(
            tab, lambda d: d.find_element(*tab).get_attribute("aria-selected") == "true",
            message=f"The '{label}' tab never became selected",
        )
        return self

    # ─── Rows ────────────────────────────────────────────────────────────────

    def rows(self) -> list[dict]:
        """The visible rows as {'title': ..., 'status': 'Draft'|'Published'|None}."""
        try:
            out = []
            for row in self.driver.find_elements(*L.ROWS):
                title = row.find_element(By.XPATH, L.ROW_TITLE).get_attribute("title")
                cells = [c.text.strip() for c in row.find_elements(By.XPATH, L.ROW_CELLS)]
                status = next((c for c in cells if c in ("Draft", "Published")), None)
                out.append({"title": title, "status": status})
            return out
        except StaleElementReferenceException:  # the table re-rendered while reading
            return self.rows()

    def titles(self) -> list[str]:
        return [r["title"] for r in self.rows()]

    def wait_for_rows(self, predicate, message: str) -> list[dict]:
        """Wait until the visible rows satisfy `predicate`, then return them."""
        def check(d):
            rows = self.rows()
            return (rows,) if predicate(rows) else False  # an empty list would read as "not yet"

        return self.wait_with_timeout(30).until(check, message=message)[0]

    def empty_message(self) -> str:
        return self.wait_with_timeout(30).until(
            EC.visibility_of_element_located(L.EMPTY_CELL), message="The table never showed an empty state"
        ).text.strip()

    def search(self, text: str) -> "ListingTablePage":
        box = self.wait.until(EC.element_to_be_clickable(L.SEARCH_INPUT))
        box.click()
        box.send_keys(Keys.CONTROL, "a")
        box.send_keys(Keys.BACKSPACE)
        if text:
            box.send_keys(text)
        return self

    # ─── Sorting ─────────────────────────────────────────────────────────────

    def sort_by_name(self) -> "ListingTablePage":
        """Click the name column header, which flips its sort direction."""
        before = self.sort_direction()
        self.click_until(
            (By.XPATH, L.SORT_BUTTON), lambda d: self.sort_direction() != before,
            message="Clicking the name column header never changed its sort direction",
        )
        return self

    def sort_direction(self) -> str:
        """'ascending', 'descending', or '' when the name column is not the sort key."""
        for el in self.driver.find_elements(By.XPATH, L.SORT_STATE):
            # .text, not textContent: the unsorted header keeps this label in the DOM, hidden.
            match = re.search(r"(ascending|descending)", el.text)
            if match:
                return match.group(1)
        return ""

    # ─── Pagination ──────────────────────────────────────────────────────────

    def page(self) -> tuple[int, int]:
        """(current page, page count) from 'Page 1 of 2'."""
        text = self.wait_with_timeout(30).until(
            EC.visibility_of_element_located(L.PAGE_STATUS), message="No 'Page X of Y' indicator"
        ).text
        current, total = re.search(r"Page (\d+) of (\d+)", text).groups()
        return int(current), int(total)

    def go_to_page(self, name: str) -> "ListingTablePage":
        """Click 'Next Page', 'Previous Page', 'First Page' or 'Last Page'."""
        before = self.page()
        button = (By.XPATH, L.PAGE_BUTTON.format(name=name))
        self.click_until(
            button, lambda d: self.page() != before,
            message=f"'{name}' never changed the page from {before}",
        )
        return self

    def page_button_enabled(self, name: str) -> bool:
        button = self.find((By.XPATH, L.PAGE_BUTTON.format(name=name)))
        return button.get_attribute("aria-disabled") != "true"

    # ─── Row actions and their confirm dialog ────────────────────────────────

    def row_action(self, title: str, action: str) -> "ListingTablePage":
        """Click a row's 'Edit', 'Unpublish' or 'Delete' button."""
        row = (By.XPATH, L.ROW_BY_TITLE.format(title=title))
        button = (By.XPATH, L.ROW_BY_TITLE.format(title=title) + "//button[starts-with(normalize-space(.),'%s')]" % action)
        self.wait_with_timeout(20).until(EC.visibility_of_element_located(row), message=f"No row titled {title!r}")
        self.click_until(button, EC.visibility_of_element_located(L.DIALOG) if action != "Edit" else (lambda d: "/edit" in d.current_url),
                         message=f"'{action}' on {title!r} had no effect")
        return self

    def dialog_text(self) -> str:
        """The open confirm dialog's heading and message."""
        heading = self.find(L.DIALOG_TITLE).text.strip()
        return f"{heading} {self.find(L.DIALOG_BODY).text.strip()}"

    def answer_dialog(self, label: str) -> "ListingTablePage":
        """Press 'Cancel' or the confirming button ('Delete', 'Unpublish') and wait for the dialog to close."""
        self.click_until(
            (By.XPATH, L.DIALOG_BUTTON.format(label=label)),
            EC.invisibility_of_element_located(L.DIALOG),
            message=f"The dialog stayed open after '{label}'",
        )
        return self
