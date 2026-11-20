# locators/consumer/publications_locators.py

from selenium.webdriver.common.by import By


class PublicationsLocators:
    """Public /publications listing and /publications/<slug> detail pages."""

    CARD_LINK = (By.XPATH, "//a[starts-with(@href, '/publications/')]")
    DETAIL_TITLE = (By.XPATH, "//main//h1[normalize-space()]")
    FILES_SECTION_ITEM = (By.XPATH, "//main//a[normalize-space()='Download'] | //main//iframe[contains(@src,'youtube')]")
