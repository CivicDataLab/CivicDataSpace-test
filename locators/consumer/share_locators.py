# locators/consumer/share_locators.py
#
# The shared SharePanel component (DataSpaceFrontend #512) used on the dataset
# page (inside the "Share dataset" popover) and in the use case story rail.

from selenium.webdriver.common.by import By


class ShareLocators:
    # Opens the panel on the dataset cover; the use case rail shows it inline.
    DATASET_TRIGGER = (By.XPATH, "//button[@aria-label='Share dataset']")

    # X, LinkedIn, Facebook and email are anchors named "Share on X" / "Share by email" ...
    LINKS = (By.XPATH, "//a[starts-with(@aria-label, 'Share ')]")
    # Copy is a button: text "Copy link" in the dataset popover, aria-label "Copy link" in the rail.
    COPY = (By.XPATH, "//button[normalize-space()='Copy link' or @aria-label='Copy link']")
    COPIED = (By.XPATH, "//button[normalize-space()='Link copied' or @aria-label='Link copied']")
    # Screen-reader status line: 'Link copied', or 'Could not copy the link' when the clipboard write fails.
    STATUS = (By.XPATH, "//p[@aria-live='polite']")
