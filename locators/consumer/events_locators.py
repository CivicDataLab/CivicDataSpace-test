# locators/consumer/events_locators.py
#
# Selectors for the public events listing (/events) and detail
# (/events/<slug>) pages (DataSpaceFrontend#515-#517).

from selenium.webdriver.common.by import By


class EventsLocators:
    # app/[locale]/(user)/events/page.tsx renders the title as a real
    # <h1> (Text ... as="h1"), unlike /privacy's styled span.
    HEADING = (By.CSS_SELECTOR, "main h1, h1")
    MAIN_CONTENT = (By.CSS_SELECTOR, "main")
    # EventCard (EventsListing.tsx) wraps each card in <Link href="/events/<slug>">.
    EVENT_CARD_LINKS = (By.CSS_SELECTOR, "a[href*='/events/']")
    EMPTY_OR_ERROR_TEXT = (By.XPATH, "//*[self::p or self::span][contains(., 'No events') or contains(., 'could not be loaded')]")


class EventDetailLocators:
    HEADING = (By.CSS_SELECTOR, "main h1, h1")
    MAIN_CONTENT = (By.CSS_SELECTOR, "main")
