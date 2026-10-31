# locators/provider/chart_wizard_locators.py
#
# The chart wizard behind "Add Chart" (DataSpaceFrontend#504):
# /charts/new (Build) -> /charts/<id>/edit/publish (Review & Publish).
# Shared wizard parts: EditorWizardLocators.

from selenium.webdriver.common.by import By

from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class ChartWizardLocators:
    ADD_CHART_BUTTON = (By.XPATH, "//main//button[normalize-space()='Add Chart']")

    DATASET_SEARCH = "//input[@placeholder='Search datasets...']"
    RESOURCE_SELECT = (By.XPATH, W.SELECT_BY_LABEL.format(label="File / Resource"))
    CHART_TYPE_CARD = "//main//button[.//*[normalize-space()='{label}']]"
    # The empty field pickers (X-axis category, then the values) read "+ Add a field".
    EMPTY_FIELD_PICKER = (By.XPATH, "//main//button[@role='combobox' and normalize-space()='+ Add a field']")

    CHART_NAME_INPUT = (By.XPATH, "//input[@name='reviewChartName']")
    PUBLISH_BUTTON = (By.XPATH, "//main//button[starts-with(normalize-space(),'Publish')]")
    PUBLISHED_TOAST = (By.XPATH, "//*[normalize-space(text())='Chart published']")
