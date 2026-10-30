# locators/provider/listing_table_locators.py
#
# The shared listing table of every provider dashboard section (datasets, use
# cases, collaboratives, AI models, publications, charts, events) since
# DataSpaceFrontend#504: status tabs with counts, search, sortable columns,
# pagination and per-row Edit / Unpublish / Delete actions.

from selenium.webdriver.common.by import By


class ListingTableLocators:
    SIDEBAR_LINK = "//aside//nav//a[.//span[normalize-space()='{section}']]"
    HEADING = "//main//h2[normalize-space()='{section}']"

    SEARCH_INPUT = (By.XPATH, "//main//input[@name='datatable-search']")

    # "All 15" / "Draft 4" / "Published 11": the label, then the count in a span.
    TAB = "//main//button[@role='tab' and starts-with(normalize-space(.),'{label}')]"
    TABS = (By.XPATH, "//main//button[@role='tab']")

    ROWS = (By.XPATH, "//main//table//tbody/tr[td[not(contains(@class,'EmptyCell'))]]")
    EMPTY_CELL = (By.XPATH, "//main//table//tbody//td[contains(@class,'EmptyCell')]")
    ROW_TITLE = ".//td[1]//span[@title]"
    ROW_CELLS = ".//td"
    ROW_BY_TITLE = "//main//table//tbody/tr[.//td[1]//span[@title='{title}']]"

    # Sortable columns render a button in the header; the first column is the name.
    SORT_BUTTON = "(//main//table//thead//th[1]//button)[1]"
    SORT_STATE = "//main//table//thead//th[1]//button//span[starts-with(normalize-space(.),'Sorted')]"

    PAGE_STATUS = (By.XPATH, "//main//span[starts-with(normalize-space(.),'Page ') and contains(.,' of ')]")
    PAGE_BUTTON = "//main//button[.//span[normalize-space()='{name}']]"

    # Confirm dialog raised by Unpublish and Delete.
    DIALOG = (By.XPATH, "//*[@role='alertdialog']")
    DIALOG_TITLE = (By.XPATH, "//*[@role='alertdialog']//h2")
    DIALOG_BODY = (By.XPATH, "//*[@role='alertdialog']//p")
    DIALOG_BUTTON = "//*[@role='alertdialog']//button[normalize-space()='{label}']"
