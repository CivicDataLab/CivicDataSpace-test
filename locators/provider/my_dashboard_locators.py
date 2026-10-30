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
    USECASES_NAV_LINK = (By.XPATH, '//span[normalize-space()="Use Cases"]')
    COLLABORATIVES_NAV_LINK = (By.XPATH, "//a[contains(@href,'/dashboard/') and contains(@href,'collaboratives')]")
    AI_MODELS_NAV_LINK = (By.XPATH, '//span[normalize-space()="AI Models"]')
    CHARTS_NAV_LINK = (By.XPATH, "//a[contains(@href,'/dashboard/') and contains(@href,'charts')]")
    PROFILE_NAV_LINK = (By.XPATH, '//span[normalize-space()="Profile"]')

    # (3) The All / Draft / Published tab strip above every listing table.
    DRAFTS_TAB = (By.XPATH, "//button[@role='tab' and contains(@id,'-trigger-DRAFT')]")

    # (4) The "Create Dataset" button in the listing header.
    ADD_NEW_DATASET_BTN = (By.XPATH, "//button[normalize-space(.)='Create Dataset']")