# tests/provider/functional/test_prv_func_203_chart_builder_validation.py
#
# Chart Build step: what Continue asks for at each stage, and the field
# mapping each chart type card shows.

import pytest

from pages.home_page import HomePage

# Chart type -> texts its Configure panel must show, and texts it must not.
TYPE_MAPPING = {
    "Bar": (["X-axis *", "Values (Y-axis) *", "Stack bars", "Orientation"], []),
    "Line": (["X-axis *", "Values (Y-axis) *", "X-axis Label"], ["Stack bars"]),
    "Treemap": (["X-axis *", "Value *"], ["Values (Y-axis) *", "X-axis Label"]),
    "Map": (["Map type", "Geographic field *", "Value *"], ["X-axis *"]),
    "Big Number": (["Value *", "Unit", "Display Label"], ["X-axis *"]),
    "Upload Image": (["Chart Image", "PNG, JPG, SVG, TIFF"], ["Configure", "X-axis *"]),
}


def open_builder(driver, base_url, test_credentials):
    email, password = test_credentials
    driver.delete_all_cookies()
    home = HomePage(driver, base_url)
    home.load()
    charts = home.go_to_login(flow="provider", email=email, password=password).goto_my_dashboard().click_charts_card()
    charts.is_loaded()
    charts.click_add_chart()
    return charts


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_203a_continue_gated_on_dataset_resource_type_and_mapping(driver, base_url, test_credentials):
    charts = open_builder(driver, base_url, test_credentials)

    charts.click_continue()
    assert "Select a dataset." in charts.page_text()

    charts.pick_first_dataset()
    charts.click_continue()
    text = charts.page_text()
    assert "Select a file or resource." in text and "Select a chart type." in text, text

    charts.pick_first_resource()
    charts.click_continue()
    text = charts.page_text()
    assert "Select a file or resource." not in text
    assert "Select a chart type." in text

    charts.choose_chart_type("Bar")
    charts.click_continue()
    text = charts.page_text()
    assert "Live Preview" in text and "Assign the required fields and save to generate a preview." in text
    assert "Review & Publish\nCheck your information" not in text, "Continue left Build with no fields mapped"


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_203b_each_chart_type_shows_its_mapping(driver, base_url, test_credentials):
    charts = open_builder(driver, base_url, test_credentials)
    charts.pick_first_dataset()
    charts.pick_first_resource()
    for chart_type, (present, absent) in TYPE_MAPPING.items():
        charts.choose_chart_type(chart_type)
        text = charts.page_text()
        for t in present:
            assert t in text, f"{chart_type}: {t!r} missing from the builder"
        for t in absent:
            assert t not in text, f"{chart_type}: {t!r} should not show"
    assert not charts.is_resource_select_shown(), "Upload Image still asks for a file / resource"


@pytest.mark.functional
@pytest.mark.timeout(420)
def test_prv_func_203c_changing_dataset_resets_resource(driver, base_url, test_credentials):
    charts = open_builder(driver, base_url, test_credentials)
    charts.pick_first_dataset()
    charts.pick_first_resource()
    assert not charts.get_resource_value().startswith("Select a file")
    charts.change_dataset()
    charts.pick_first_dataset()
    assert charts.get_resource_value().startswith("Select a file"), (
        f"Resource kept {charts.get_resource_value()!r} after the dataset was changed"
    )
