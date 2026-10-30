# locators/consumer/dataset_detail_locators.py
#
# Dataset detail page (/datasets/<id>) as revamped in DataSpaceFrontend #512:
# a cover, then four tabs (Data, Visualisations, Metadata, Connected to). The
# tabs are role=tab buttons with ids dataset-tab-<name>; every panel stays in
# the DOM and is hidden until its tab is selected.

from selenium.webdriver.common.by import By


class DatasetDetailLocators:
    @staticmethod
    def tab(name):
        return (By.ID, f"dataset-tab-{name}")

    @staticmethod
    def panel(name):
        return (By.ID, f"dataset-tab-panel-{name}")

    # The heading each panel opens with. Metadata's depends on the record
    # having a description, so its stable heading is "Dataset information".
    PANEL_HEADING = {
        "data": (By.XPATH, "//div[@id='dataset-tab-panel-data']//h2[normalize-space()='Data files']"),
        "visualisations": (By.XPATH, "//div[@id='dataset-tab-panel-visualisations']//h2[normalize-space()='Visualisations']"),
        "metadata": (By.XPATH, "//div[@id='dataset-tab-panel-metadata']//h3[normalize-space()='Dataset information']"),
        "connected": (By.XPATH, "//div[@id='dataset-tab-panel-connected']//h2[normalize-space()='Where this dataset is used']"),
    }

    # Data tab: file tree (files are buttons without aria-expanded; folders have it),
    # then the selected file's title, fact line and Download link.
    FILE_BUTTONS = (By.XPATH, "//div[@id='dataset-tab-panel-data']//ul//li/button[not(@aria-expanded)]")
    FILE_TITLE = (By.XPATH, "//div[@id='dataset-tab-panel-data']//h3")
    FILE_FACT_LINE = (By.XPATH, "//div[@id='dataset-tab-panel-data']//h3/following-sibling::p")
    FILE_DOWNLOAD = (By.XPATH, "//div[@id='dataset-tab-panel-data']//a[normalize-space()='Download']")

    # Visualisations tab: one <article> per chart, its name is the card's button label.
    CHART_NAMES = (By.XPATH, "//div[@id='dataset-tab-panel-visualisations']//article//button/span[1]/span")
    NO_CHARTS = (By.XPATH, "//div[@id='dataset-tab-panel-visualisations']//p[normalize-space()='No visualisations yet']")

    # Metadata tab
    ABOUT_TEXT = (By.XPATH, "//div[@id='dataset-tab-panel-metadata']//h3[normalize-space()='About this dataset']/following-sibling::div")
    INFO_LABELS = (By.XPATH, "//div[@id='dataset-tab-panel-metadata']//p[contains(@class,'uppercase')]")
    TAG_LINKS = (By.XPATH, "//div[@id='dataset-tab-panel-metadata']//a[contains(@href,'/search?types=dataset&tags=')]")

    # Connected tab
    FILTER_BUTTONS = (By.XPATH, "//div[@id='dataset-tab-panel-connected']//div[@role='group']/button")
    GROUP_HEADINGS = (By.XPATH, "//div[@id='dataset-tab-panel-connected']//section/h3")
    CARD_LINKS = (By.XPATH, "//div[@id='dataset-tab-panel-connected']//section//a[@href]")
    NOTHING_CONNECTED = (By.XPATH, "//div[@id='dataset-tab-panel-connected']//p[normalize-space()='Nothing is connected yet']")
