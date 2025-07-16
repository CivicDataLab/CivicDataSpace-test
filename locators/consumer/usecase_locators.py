# locators/consumer/usecase_locators.py

class UseCaseLocators:
    """XPaths for elements on the Use Cases page."""

    # The page header (“Our Use Cases”)
    HEADER = "/html/body/main/div/main/div[2]/div/div/span[1]"

    # All usecase‐card containers
    CARD = "/html/body/main/div/main/div[3]/div[2]"

    #First UseCase
    UC_FIRST_CARD = "/html/body/main/div/main/div[3]/div[2]/a[1]"

    #First Dataset under Usecase
    UC_DATASET_FIRST_CARD = "/html/body/main/div/div/div[2]/div[2]/div[2]/a"

    #Download link for dataset under use case.
    DOWNLOAD_LINK = "//a[@class='flex justify-center']"
