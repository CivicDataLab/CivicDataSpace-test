# locators/consumer/usecase_locators.py
# Optimized with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class UseCaseLocators:
    """XPaths for elements on the Use Cases page."""

    # The page header ("Our Use Cases")
    HEADER = (By.XPATH, "//main//span[contains(., 'Use Case') or contains(., 'UseCases')] | //main//h1[contains(., 'Use Case')]")

    # All usecase-card containers
    CARD = (By.XPATH, "//main//a[@href[contains(., '/usecases/')]]")

    # First UseCase - clickable link
    UC_FIRST_CARD = (By.XPATH, "//a[@href[contains(., '/usecases/')]]")

    # First Dataset under Usecase.
    # NOT scoped to a 'datasets_List' container — that CSS-module class no longer
    # exists in the rendered DOM, which made the download test silently skip.
    UC_DATASET_FIRST_CARD = (By.XPATH, "//main//a[@href[contains(., '/datasets/')]]")

    # Download link for the dataset resource under a use case.
    # Scoped to /download/resource/ so it targets the dataset file, not the
    # chart-image link (/download/chart/), which is a separate failing endpoint.
    DOWNLOAD_LINK = (By.XPATH, "//a[contains(@href, '/download/resource/')]")

    # Use case detail page (/usecases/<id>): dashboards embedded as iframes (DataSpaceFrontend #476)
    DETAIL_DATASETS_HEADING = (By.XPATH, "//main//*[normalize-space(text())='Datasets in this Use Case']")
    DETAIL_DASHBOARDS_HEADING = (By.XPATH, "//main//*[normalize-space(text())='Dashboards Linked to this Use Case']")
    DETAIL_DASHBOARD_IFRAME = (By.XPATH, "//main//iframe")
    DETAIL_DASHBOARD_OPEN_LINK = (By.XPATH, "//main//a[normalize-space()='Open dashboard in a new tab']")
