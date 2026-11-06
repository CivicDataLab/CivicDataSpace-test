# locators/provider/charts_locators.py
from selenium.webdriver.common.by import By


class ChartsLocators:
    # Charts list page
    SHOWING_CHARTS_HEADING = (By.XPATH, "//*[normalize-space()='Showing Charts']")
    ADD_CHART_BTN = (By.XPATH, "//button[normalize-space()='Add Chart']")

    # Chart editor panel (appears inline; "Create Chart" is unique to the CHART sub-panel)
    CHARTS_EDITOR_HEADING = (By.XPATH, "//*[normalize-space()='Charts Editor']")

    # Dataset/Resource selects — scoped to the CHART sub-panel via the unique "Create Chart" button
    CHART_SELECT_DATASET = (By.XPATH, "(//div[.//button[normalize-space()='Create Chart']]//select)[1]")
    CHART_SELECT_RESOURCE = (By.XPATH, "(//div[.//button[normalize-space()='Create Chart']]//select)[2]")

    # Chart type buttons
    CHART_TYPE_BAR      = (By.XPATH, "//button[normalize-space()='BAR']")
    CHART_TYPE_LINE     = (By.XPATH, "//button[normalize-space()='LINE']")
    CHART_TYPE_TREEMAP  = (By.XPATH, "//button[normalize-space()='TREEMAP']")

    # Actions
    CREATE_CHART_BTN = (By.XPATH, "//button[normalize-space()='Create Chart']")

    # Chart detail editor (opened after creating / clicking an existing chart)
    CHART_DETAIL_DATA_TAB   = (By.XPATH, "//button[normalize-space()='DATA']")
    CLOSE_CHART_EDITOR_BTN  = (By.XPATH, "(//a | //button)[contains(normalize-space(),'Close Editor')]")

    # New chart wizard (Build > Review & Publish), 2026-11 redesign
    DATASET_SEARCH_INPUT = (By.XPATH, "//input[starts-with(@placeholder,'Search datasets')]")
    DATASET_RESULT = (By.XPATH, "(//button[contains(@class,'entity-row-picker')])[1]")
    SELECTED_DATASET_TITLE = (By.XPATH, "//*[normalize-space()='Dataset *' or normalize-space()='Dataset']/following::p[1]")
    RESOURCE_COMBOBOX = (By.XPATH, "//label[contains(normalize-space(),'File / Resource')]/following::button[@role='combobox'][1]")
    RESOURCE_OPTION = (By.XPATH, "//*[@role='listbox']//*[@role='option']")
    CONTINUE_BTN = (By.XPATH, "//button[normalize-space()='Continue']")
    @staticmethod
    def chart_type_card(name):
        return (By.XPATH, f"//button[.//*[normalize-space()='{name}']]")
    CHANGE_DATASET_BTN = (By.XPATH, "//main//button[normalize-space()='Change']")
    MAIN = (By.TAG_NAME, "main")
    LIVE_PREVIEW_HEADING = (By.XPATH, "//*[normalize-space()='Live Preview']")
