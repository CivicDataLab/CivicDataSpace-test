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
