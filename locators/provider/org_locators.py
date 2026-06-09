# locators/provider/org_locators.py

from selenium.webdriver.common.by import By
from locators.provider.my_dashboard_locators import MyDashboardLocators

class OrgLocators:
    """
    XPaths for the "Provider → Org Dashboard" flow.

    After selecting an organization, the URL redirects to:
    /dashboard/organization/{org-name}/dataset

    The dashboard structure after org selection is IDENTICAL to MyDashboard,
    so we reuse those locators.
    """

    # The organization card on the organizations list page
    # Using ID selector for more reliable targeting
    ORG_TEST = (By.XPATH, '//a[@id="my-test-agency"]')

    # Alternative: using text-based selector (less reliable)
    # ORG_TEST = (By.XPATH, '//span[normalize-space()="my test agency"]')

    # After selecting org, the dashboard UI is identical to MyDashboard
    # So we reuse all the locators from MyDashboardLocators
    SIDEBAR_DATASETS = MyDashboardLocators.SIDEBAR_DATASETS
    DRAFTS_TAB = MyDashboardLocators.DRAFTS_TAB
    ADD_NEW_DATASET_BTN = MyDashboardLocators.ADD_NEW_DATASET_BTN
    USECASES_NAV_LINK = MyDashboardLocators.USECASES_NAV_LINK
    COLLABORATIVES_NAV_LINK = MyDashboardLocators.COLLABORATIVES_NAV_LINK
    AI_MODELS_NAV_LINK = MyDashboardLocators.AI_MODELS_NAV_LINK
    PROFILE_NAV_LINK = MyDashboardLocators.PROFILE_NAV_LINK
