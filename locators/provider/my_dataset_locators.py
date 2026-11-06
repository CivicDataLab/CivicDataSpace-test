# locators/provider/my_dashboard_locators.py

class MyDatasetLocators:

    ADD_NEW_DATASET_BTN = "//button[normalize-space(.)='Create Dataset' and not(ancestor::*[@role='dialog'])]"
    # you can also verify the Drafts tab is up
    DRAFTS_TAB = "//button[starts-with(normalize-space(.),'Draft')]"