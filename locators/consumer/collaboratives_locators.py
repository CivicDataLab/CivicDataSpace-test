# locators/consumer/collaboratives_locators.py

from selenium.webdriver.common.by import By


class CollaborativesLocators:
    """Selectors for the public Collaboratives listing page."""

    # Card images are served from the storage CDN; header/hero images are not.
    CARD_IMAGE = (By.XPATH, "//img[contains(@src,'cloudfront') or contains(@src,'/dev/public/')]")
    IMAGE = (By.TAG_NAME, "img")
