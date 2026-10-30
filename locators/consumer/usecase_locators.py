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

    # Use case detail page (/usecases/<id>), as revamped in DataSpaceFrontend #512.
    # The cover <h1> renders for every published use case, so it is the "page
    # loaded" anchor. Both content sections are conditional: "Explore the data"
    # exists only when a dashboard is embeddable, "Datasets behind this story"
    # only when the use case has datasets.
    DETAIL_TITLE = (By.XPATH, "//main//h1")
    DETAIL_DATASETS_HEADING = (By.XPATH, "//main//h2[normalize-space()='Datasets behind this story']")
    DETAIL_DASHBOARDS_HEADING = (By.XPATH, "//main//h2[normalize-space()='Explore the data']")
    DETAIL_DASHBOARD_IFRAME = (By.XPATH, "//main//iframe")

    # Use case cover, story rail, dataset cards and topic chips (DataSpaceFrontend #512)
    COVER_BACK = (By.XPATH, "//main//a[normalize-space()='Back']")
    COVER_META = (By.XPATH, "//main//a[normalize-space()='Back']/following-sibling::div[1]")
    COVER_PUBLISHER = (By.XPATH, "//main//a[.//span[normalize-space()='Organisation' or normalize-space()='Individual']]")
    CONTENTS_LINKS = (By.XPATH, "//main//nav[@aria-label='Contents']//a")
    CONTRIBUTOR_LINKS = (By.XPATH, "//main//section[@aria-label='Contributors']//li//a")
    DATASET_CARD_LINKS = (By.XPATH, "//main//h2[normalize-space()='Datasets behind this story']/following-sibling::ul//li//a")

    @staticmethod
    def topic_links(group_title):
        """Chips under a TopicBar group titled 'Tags', 'SDG Goals' or 'Sector'."""
        return (By.XPATH, f"//main//p[normalize-space()='{group_title}']/following-sibling::div[1]//a")

    # JusticeHub dashboard embed (DataSpaceFrontend #492): a justicehub.in dashboard
    # gets its own wrapper that preloads the public theme CSS/logo and hides the
    # iframe behind a spinner (aria-busy) until it has actually loaded, instead of
    # the plain iframe every other dashboard still uses.
    JUSTICEHUB_PRELOAD_CSS = (By.XPATH, "//link[@rel='preload' and contains(@href, 'jh_home_new1.css')]")
    JUSTICEHUB_PRELOAD_LOGO = (By.XPATH, "//link[@rel='preload' and contains(@href, 'jh_logo.png')]")
    JUSTICEHUB_PRECONNECT = (By.XPATH, "//link[@rel='preconnect' and contains(@href, 'justicehub.in')]")
    # The wrapper div carries aria-busy and contains the iframe it is guarding.
    JUSTICEHUB_EMBED_WRAPPER = (By.XPATH, "//main//div[@aria-busy][.//iframe]")
