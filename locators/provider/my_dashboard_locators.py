# locators/provider/my_dashboard_locators.py

class MyDashboardLocators:
    """
    XPaths for the “Provider → My Dashboard” flow.
    """

    # (1) The two big landing cards on /dashboard when you first log in
    CARD_MY_DASHBOARD = "//a[contains(@href,'/dashboard') and .//span[normalize-space()='My Dashboard']]"

    # (3) Inside the “Datasets” panel, the “Drafts” tab is visible by default.
    DRAFTS_TAB = "//span[normalize-space(.)='Drafts']"

    # (4) The orange “Add New Dataset” button lives inside the “Drafts” tab panel.
    ADD_NEW_DATASET_BTN = "(//button[normalize-space(.)='Add New Dataset'])[2]"

    USECASES_NAV_LINK = '//span[normalize-space()="UseCases"]'

    #Profile tab locators
    PROFILE_NAV_LINK = '//span[normalize-space()="Profile"]'