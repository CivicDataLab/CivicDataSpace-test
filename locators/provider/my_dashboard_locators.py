# locators/provider/my_dashboard_locators.py

from selenium.webdriver.common.by import By

class MyDashboardLocators:
    """
    XPaths for the "Provider → My Dashboard" flow.
    """

    # (1) The two big landing cards on /dashboard when you first log in
    CARD_MY_DASHBOARD = (By.XPATH, "//a[contains(@href,'/dashboard') and .//span[normalize-space()='My Dashboard']]")

    # (2) Sidebar navigation links
    SIDEBAR_DATASETS = (By.XPATH, '//span[normalize-space()="Datasets"]')
    USECASES_NAV_LINK = (By.XPATH, '//span[normalize-space()="UseCases"]')
    COLLABORATIVES_NAV_LINK = (By.XPATH, "//a[contains(@href,'/dashboard/') and contains(@href,'collaboratives')]")
    AI_MODELS_NAV_LINK = (By.XPATH, '//span[normalize-space()="AI Models"]')
    CHARTS_NAV_LINK = (By.XPATH, "//a[contains(@href,'/dashboard/') and contains(@href,'charts')]")
    PROFILE_NAV_LINK = (By.XPATH, '//span[normalize-space()="Profile"]')

    # (3) Inside the "Datasets" panel, the "Drafts" tab is visible by default.
    DRAFTS_TAB = (By.XPATH, "//span[normalize-space(.)='Drafts']")

    # (4) The orange "Add New Dataset" button lives inside the "Drafts" tab panel.
    ADD_NEW_DATASET_BTN = (By.XPATH, "//button[normalize-space(.)='Add New Dataset']")