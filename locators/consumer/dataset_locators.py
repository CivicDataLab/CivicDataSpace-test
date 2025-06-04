# locators/consumer/dataset_locators.py

class DatasetLocators:
    """XPaths for elements on the Datasets page."""

    # All dataset‐card containers
    CARD = "/html/body/main/div/div/div[2]/div/div/div[2]/div[2]/div[1]"

    # (Optional) first card only
    FIRST_CARD = "/html/body/main/div/div/div[2]/div/div/div[2]/div[2]/div[1]/a[1]"

    # The “Download” link inside a dataset‐card
    DOWNLOAD_LINK = "/html/body/main/div/main/div[2]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div/div/div[2]/div/div[1]/div/a"
