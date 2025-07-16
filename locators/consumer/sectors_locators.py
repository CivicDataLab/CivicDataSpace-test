# locators/consumer/sectors_locators.py

class SectorsLocators:
    """XPaths for elements on the Sectors page."""

    # The page header (“Our Sectors”)
    HEADER = "/html/body/main/div/main/div[2]/div[1]/div/div[1]/span[1]"

    # All sector‐card containers
    SEC_CARD = "/html/body/main/div/main/div[2]/div[2]/div[2]"

    # First Sector Card
    SEC_FIRST_CARD = "/html/body/main/div/main/div[2]/div[2]/div[2]/a[1]"

    #ALL dataset card under a sector page
    SEC_DATASET_CARD = "/html/body/main/div/div/div[2]/div[2]/div/div[2]/div[3]/div[1]"

    #First dataset card under a sector page
    SEC_DATASET_FIRST_CARD = "/html/body/main/div/div/div[2]/div[2]/div/div[2]/div[3]/div[1]/a[1]"

    #download link of the first dataset
    DOWNLOAD_LINK = "//a[@class='flex justify-center']"