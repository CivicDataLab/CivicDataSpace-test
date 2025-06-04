# locators/provider/my_dashboard_locators.py

class MyDatasetLocators:

    ADD_NEW_DATASET_BTN = "//span[normalize-space(.)='Add New Dataset']/ancestor::button[1]"
    # you can also verify the Drafts tab is up
    DRAFTS_TAB = "//span[normalize-space(.)='Drafts']"