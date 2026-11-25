# tests/provider/functional/test_prv_func_211_chart_ui.py
#
# The chart wizard and listing, beyond what 203 (builder gating) and 024
# (happy path) cover: what each chart type asks for when Continue is pressed
# empty, what Review & Publish says about readiness, and the lifecycle a
# published chart goes through in the listing (Unpublish, Edit, Delete).
# 211a creates nothing. 211b creates one org chart and the `cleanup` fixture
# deletes it whatever happened.

import uuid

import pytest
from selenium.webdriver.common.by import By

from locators.provider.editor_wizard_locators import EditorWizardLocators as W
from pages.provider.chart_wizard_page import ChartWizardPage
from pages.provider.listing_table_page import ListingTablePage
from tests.provider.functional.test_prv_func_203_chart_builder_validation import open_builder
from tests.provider.smoke.test_prv_024_org_chart_and_publication_wizards import _published_dataset_with_a_file

pytestmark = pytest.mark.functional

NEEDS_X_AND_Y = ["Choose a field for the category axis.", "Choose at least one numeric value."]
EMPTY_BUILD = {
    "Bar": NEEDS_X_AND_Y,
    "Line": NEEDS_X_AND_Y,
    "Treemap": NEEDS_X_AND_Y,
    "Big Number": ["Choose the number to highlight."],
    "Map": ["Choose the geographic field.", "Choose the value that colours the map."],
}
MAP_TYPES = {
    "Point map": ["Choose latitude and longitude fields."],
    "Polygon map": ["Choose the polygon field."],
    "Geospatial map": ["Choose the geospatial field."],
}


@pytest.mark.timeout(480)
def test_prv_func_211a_each_chart_type_names_what_it_still_needs(driver, base_url, test_credentials):
    """Continue with nothing mapped says what each chart type is missing, and Upload Image asks for an image only."""
    charts = open_builder(driver, base_url, test_credentials)
    charts.pick_first_dataset()
    charts.pick_first_resource()
    for chart_type, expected in EMPTY_BUILD.items():
        charts.choose_chart_type(chart_type)
        charts.click_continue()
        text = charts.page_text()
        missing = [m for m in expected if m not in text]
        assert not missing, f"{chart_type}: Continue did not say {missing}"
        assert "Review & Publish\nCheck your information" not in text, f"{chart_type}: Continue left Build with nothing mapped"

    wizard = ChartWizardPage(driver)
    for map_type, expected in MAP_TYPES.items():
        wizard.choose_select_option((By.XPATH, W.SELECT_BY_LABEL.format(label="Map type")), map_type)
        charts.click_continue()
        text = charts.page_text()
        missing = [m for m in expected if m not in text]
        assert not missing, f"{map_type}: Continue did not say {missing}"

    charts.choose_chart_type("Upload Image")
    charts.click_continue()
    text = charts.page_text()
    assert "Upload a chart image." in text, "Upload Image did not ask for an image"
    assert "Select a file or resource." not in text, "Upload Image asked for a file / resource"


@pytest.mark.timeout(900)
def test_prv_func_211b_review_readiness_and_the_published_chart_lifecycle(
    driver, open_listing, provider_api, cleanup, writable_org
):
    """
    A new chart gets a default name; emptying it blocks publishing until it is named. Once published, its listing row
    offers Unpublish and Delete but not Edit; Unpublish returns it to Draft, where Edit reopens it with its
    mapping, and Delete asks first and only removes the chart on confirmation.
    """
    dataset = _published_dataset_with_a_file(provider_api, writable_org)
    if not dataset:
        pytest.skip(f"{writable_org} has no published dataset with a file to chart")
    cleanup.watch("chart", writable_org)
    name = f"zz-auto-chart-{uuid.uuid4().hex[:8]}"

    open_listing("org", "Charts")
    wizard = ChartWizardPage(driver).start()
    wizard.pick_dataset(dataset)
    wizard.choose_first_resource()
    wizard.choose_chart_type("Bar")
    x_field = wizard.fill_next_field()
    y_field = wizard.fill_next_field()
    wizard.continue_to_review()

    review = wizard.page_text()
    assert "Chart name added" in review and "Dataset selected" in review, f"Review shows no checklist: {review[:500]}"
    assert wizard.chart_name().startswith("New chart"), f"A new chart is not given a default name: {wizard.chart_name()!r}"
    assert wizard.is_publish_enabled(), "Publish Changes was disabled for a complete, default-named chart"
    wizard.clear_chart_name()
    assert not wizard.is_publish_enabled(), "Publish Changes was enabled for a chart with no name"
    wizard.name_chart(name)
    assert wizard.is_publish_enabled(), "Publish Changes stayed disabled after the chart was named"
    wizard.publish()

    table = ListingTablePage(driver).open_section("Charts")
    table.search(name)
    rows = table.wait_for_rows(lambda r: [x["title"] for x in r] == [name], f"The chart {name!r} is not listed")
    assert rows[0]["status"] == "Published"
    buttons = " | ".join(table.row_buttons(name))
    assert "Unpublish" in buttons and "Delete" in buttons, f"A published row offers {buttons!r}"
    assert "Edit" not in buttons, f"A published chart offers Edit: {buttons!r}"

    table.row_action(name, "Unpublish")
    assert "Unpublish chart?" in table.dialog_text(), f"The dialog says {table.dialog_text()!r}"
    table.answer_dialog("Unpublish")
    assert table.toast_shown("Unpublished chart successfully"), "No toast after unpublishing"
    table.wait_for_rows(lambda r: [(x["title"], x["status"]) for x in r] == [(name, "Draft")], "The chart did not return to Draft")

    table.row_action(name, "Edit")
    wizard = ChartWizardPage(driver)
    text = wizard.wait_with_timeout(30).until(lambda d: (t := wizard.page_text()) and x_field in t and y_field in t and t)
    assert "Bar" in text, "The reopened chart lost its chart type"

    table = ListingTablePage(driver).open_section("Charts")
    table.search(name)
    table.wait_for_rows(lambda r: [x["title"] for x in r] == [name], f"The chart {name!r} is not listed")
    table.row_action(name, "Delete")
    dialog = table.dialog_text()
    assert "Delete chart?" in dialog and "cannot be undone" in dialog, f"The dialog says {dialog!r}"
    table.answer_dialog("Cancel")
    assert table.titles() == [name], "Cancel removed the chart"
    table.row_action(name, "Delete")
    table.answer_dialog("Delete")
    assert table.toast_shown("Deleted chart successfully"), "No toast after deleting"
    table.wait_for_rows(lambda r: not r, f"The chart {name!r} is still listed after Delete")
