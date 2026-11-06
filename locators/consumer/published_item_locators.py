# locators/consumer/published_item_locators.py
#
# Generic selectors for anonymous consumer pages (dataset / use case /
# collaborative / AI model detail pages and their listings).

from selenium.webdriver.common.by import By


class PublishedItemLocators:
    BODY = (By.TAG_NAME, "body")
    TAB = "//*[@role='tab' or self::button][normalize-space()='{}']"
    IMAGES_WITH_ALT = (By.CSS_SELECTOR, "img[alt]")
    EXTERNAL_LINKS = (By.CSS_SELECTOR, "a[href^='http']")
    # Listing has finished loading: either the pager or an empty-state message.
    LISTING_SETTLED_TEXTS = ("Page 1 of", "No datasets found", "No collaboratives found", "Try adjusting")
    NOT_FOUND_TEXTS = ("Page not found", "could not be loaded", "could not be found", "not found", "Not Found")
