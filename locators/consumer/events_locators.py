# locators/consumer/events_locators.py

from selenium.webdriver.common.by import By


class EventsLocators:
    """Selectors for the public Events listing and detail pages."""

    LISTING_HEADER = (By.XPATH, "//h1[normalize-space(text())='Events']")
    CARD_LINK = (By.XPATH, "//a[starts-with(@href, '/events/') and @href != '/events']")
    DETAIL_HEADER = (By.TAG_NAME, "h1")
    LUMA_IFRAME = (By.XPATH, "//iframe[contains(@src, 'luma.com/embed/event/')]")
