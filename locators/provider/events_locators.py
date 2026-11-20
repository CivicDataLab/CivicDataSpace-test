# locators/provider/events_locators.py
#
# The event editor (DataSpaceFrontend events wizard): Details -> Review & Publish.
# Shared wizard parts (stepper, Continue, inline errors) are in EditorWizardLocators.

from selenium.webdriver.common.by import By


class EventsLocators:
    NAME_INPUT = (By.XPATH, "//input[@name='eventName']")
    LOCATION_INPUT = (By.XPATH, "//input[@name='eventLocation']")
    START_DATE_INPUT = (By.XPATH, "//input[@name='eventStartDate']")
    END_DATE_INPUT = (By.XPATH, "//input[@name='eventEndDate']")
    EMBED_INPUT = (By.XPATH, "//textarea[@name='lumaEmbed']")

    # Review & Publish: "NAME"/"LOCATION"/... captions over each value, a checklist, one Publish button.
    PREVIEW_VALUE = "//main//*[normalize-space(text())='{caption}']/following-sibling::*[1]"
    READINESS = (By.XPATH, "//main//*[normalize-space(text())='Ready to publish' or normalize-space(text())='Needs attention']")
    PUBLISH_BUTTON = (By.XPATH, "//main//button[normalize-space()='Publish' or normalize-space()='Published']")
    PREVIEW_IFRAME = (By.XPATH, "//main//iframe")
