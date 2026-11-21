# pages/provider/event_editor_page.py
#
# Event editor. Unlike the other editors, its fields do not save on blur: the
# Details step saves everything when Continue (or a step) is pressed.

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from locators.provider.events_locators import EventsLocators as L
from pages.provider.editor_wizard_page import EditorWizardPage


class EventEditorPage(EditorWizardPage):
    ENTITY = "Event"
    DRAFT_FIELD = L.LOCATION_INPUT

    def fill(self, name=None, location=None, start=None, end=None, embed=None):
        """Set the given Details fields; dates are YYYY-MM-DD."""
        for locator, value in ((L.NAME_INPUT, name), (L.LOCATION_INPUT, location), (L.EMBED_INPUT, embed)):
            if value is not None:
                self.clear_and_type(locator, value)
        if start is not None:
            self.enter_date(L.START_DATE_INPUT, start)
        if end is not None:
            self.enter_date(L.END_DATE_INPUT, end)
        return self

    def values(self) -> dict:
        get = lambda loc: self.find(loc).get_attribute("value")
        return {"name": get(L.NAME_INPUT), "location": get(L.LOCATION_INPUT), "start": get(L.START_DATE_INPUT),
                "end": get(L.END_DATE_INPUT), "embed": get(L.EMBED_INPUT)}

    def continue_to_review(self):
        return self.click_continue("preview")

    # ── Review & Publish ──────────────────────────────────────────────────────

    def preview_value(self, caption: str) -> str:
        """The value under a caption such as 'LOCATION' or 'PUBLIC LINK'."""
        return self.find((By.XPATH, L.PREVIEW_VALUE.format(caption=caption))).text.strip()

    def readiness(self) -> str:
        return self.find(L.READINESS).text.strip()

    def preview_iframe_src(self) -> str:
        return self.find(L.PREVIEW_IFRAME).get_attribute("src")

    def publish_button(self):
        return self.wait.until(EC.presence_of_element_located(L.PUBLISH_BUTTON))

    def is_publish_enabled(self) -> bool:
        """The design-system button marks itself disabled with aria-disabled, not `disabled`."""
        btn = self.publish_button()
        return btn.get_attribute("aria-disabled") != "true" and btn.is_enabled()

    def publish(self):
        btn = self.publish_button()
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        self.wait_with_timeout(20).until(
            lambda d: self.publish_button().text.strip() == "Published", message="The event never showed as Published")
        return self
