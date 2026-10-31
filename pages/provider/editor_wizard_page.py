# pages/provider/editor_wizard_page.py

import os
import re

from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class EditorWizardPage(BasePage):
    """Steps, fields and publishing shared by the entity editor wizards (see W)."""

    ENTITY = ""  # "Use Case", "Collaborative", ... as in "Publish <ENTITY>"

    # ─── Classification fields ──────────────────────────────────────────────────

    def select_field_options(self, label: str, values: list[str]):
        for val in values:
            self.select_combobox_option((By.XPATH, W.FIELD_INPUT.format(label=label)), val)
        return self

    def selected_chips(self, label: str) -> list[str]:
        self.wait.until(EC.presence_of_element_located((By.XPATH, W.FIELD_INPUT.format(label=label))))
        return [el.get_attribute("title")
                for el in self.driver.find_elements(By.XPATH, W.FIELD_CHIPS.format(label=label))]

    def select_sectors(self, items: list[str]):
        return self.select_field_options("Sectors", items)

    def select_sdg_goals(self, value: str):
        return self.select_field_options("SDG Goals", [value])

    def select_tags(self, items: list[str]):
        return self.select_field_options("Tags", items)

    def select_geography(self, name: str):
        """Pick the geography called `name`, whatever parent its option shows."""
        self.wait_until_saved()
        combo = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, W.FIELD_INPUT.format(label="Geography")))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", combo)
        combo.click()
        combo.send_keys(name)
        option = (By.XPATH, W.GEOGRAPHY_OPTION.format(listbox=combo.get_attribute("aria-controls"), name=name))
        self.wait_with_timeout(30).until(
            EC.element_to_be_clickable(option), message=f"No geography option for {name!r}"
        ).click()
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()  # the combo re-renders on select
        self.wait_for_autosave(trigger_blur=False)
        return self

    def get_selected_sectors(self) -> list[str]:
        return self.selected_chips("Sectors")

    def get_selected_sdg_goals(self) -> list[str]:
        return self.selected_chips("SDG Goals")

    def get_selected_tags(self) -> list[str]:
        return self.selected_chips("Tags")

    def get_selected_geography(self) -> list[str]:
        return self.selected_chips("Geography")

    # ─── Button-style selects (Radix: they open on a real pointer press) ───────

    def _open_select(self, trigger_locator):
        self.wait_until_saved()
        trigger = self.wait.until(EC.element_to_be_clickable(trigger_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
        trigger.click()
        listbox = self.wait.until(lambda d: trigger.get_attribute("aria-controls") or False)
        return trigger, listbox

    def choose_select_option(self, trigger_locator, text: str):
        trigger, listbox = self._open_select(trigger_locator)
        self.wait_with_timeout(15).until(
            EC.element_to_be_clickable((By.XPATH, W.SELECT_OPTION.format(listbox=listbox, text=text))),
            message=f"No {text!r} option in the select",
        ).click()
        self.wait_with_timeout(10).until(
            lambda d: text in trigger.text, message=f"The select never showed {text!r}"
        )
        return self

    def get_select_options(self, trigger_locator) -> list[str]:
        _, listbox = self._open_select(trigger_locator)
        options = self.wait_with_timeout(30).until(
            lambda d: d.find_elements(By.XPATH, W.LISTBOX_OPTIONS.format(listbox=listbox)) or False,
            message="The select listed no options",
        )
        values = [o.get_attribute("textContent").strip() for o in options]
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return values

    # ─── Images ─────────────────────────────────────────────────────────────────

    def upload_image(self, label: str, path_to_file: str):
        """Upload into the `label` image field and wait for its preview."""
        self.wait_until_saved()
        field = self.wait.until(
            EC.presence_of_element_located((By.XPATH, W.IMAGE_FILE_INPUT.format(label=label)))
        )
        field.send_keys(os.path.abspath(path_to_file))
        self.wait_with_timeout(30).until(
            EC.visibility_of_element_located((By.XPATH, W.IMAGE_PREVIEW.format(label=label))),
            message=f"No '{label}' preview after uploading {os.path.basename(path_to_file)}",
        )
        self.wait_until_saved()
        return self

    # ─── Connecting published items ─────────────────────────────────────────────

    def connect_first(self, placeholder: str, heading: str) -> str:
        """Open the picker, connect its first result, return that result's title."""
        search = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, W.PICKER_SEARCH.format(placeholder=placeholder)))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search)
        search.click()
        first = self.wait_with_timeout(30).until(
            EC.element_to_be_clickable(W.PICKER_RESULT),
            message=f"The {heading} picker listed no published items",
        )
        title = first.text.split("\n")[0].strip()
        first.click()
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(
                (By.XPATH, W.CONNECTED_TITLE.format(heading=heading, title=title))
            ),
            message=f"'{title}' never showed as connected under {heading}",
        )
        self.wait_until_saved()  # the card shows before the autosave lands; a reload now would lose it
        return title

    def connect_first_dataset(self) -> str:
        return self.connect_first("Search published datasets...", "Datasets")

    def remove_chip(self, label: str, value: str):
        self.wait_until_saved()
        btn = self.find((By.XPATH, W.CHIP_REMOVE.format(label=label, value=value)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()
        self.wait_with_timeout(10).until(
            lambda d: value not in self.selected_chips(label), message=f"'{value}' chip never went away"
        )
        self.wait_for_autosave(trigger_blur=False)
        return self

    def search_picker(self, placeholder: str, text: str):
        search = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, W.PICKER_SEARCH.format(placeholder=placeholder)))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search)
        search.click()
        search.send_keys(text)
        return self

    def get_picker_empty_text(self) -> str:
        return self.wait_with_timeout(30).until(
            EC.visibility_of_element_located(W.PICKER_EMPTY), message="The picker never showed an empty state"
        ).text.strip()

    def remove_connected(self, title: str):
        self.wait_until_saved()
        btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, W.REMOVE_CONNECTED.format(title=title))))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()
        self.wait_with_timeout(20).until(
            EC.invisibility_of_element_located((By.XPATH, W.REMOVE_CONNECTED.format(title=title))),
            message=f"'{title}' stayed connected",
        )
        self.wait_until_saved()
        return self

    def is_connected(self, heading: str, title: str, timeout: int = 10) -> bool:
        """Whether `title` shows under `heading`; connected cards load after the form."""
        try:
            self.wait_with_timeout(timeout).until(EC.presence_of_element_located(
                (By.XPATH, W.CONNECTED_TITLE.format(heading=heading, title=title))))
            return True
        except TimeoutException:
            return False

    # ─── Validation state ───────────────────────────────────────────────────────

    def get_inline_errors(self) -> list[str]:
        return list(dict.fromkeys(e.text.strip() for e in self.finds(W.INLINE_ERRORS) if e.text.strip()))

    def get_step_text(self, label: str) -> str:
        """The stepper button's text, e.g. 'Metadata Name, ... Incomplete'."""
        return " ".join(self.find((By.XPATH, W.STEP.format(label=label))).text.split())

    def get_page_text(self) -> str:
        return self.find((By.TAG_NAME, "main")).text

    def press_continue(self):
        """Click Continue without expecting it to move on; returns once the click settled."""
        self.wait_until_saved()
        btn = self.wait.until(EC.element_to_be_clickable(W.CONTINUE_BUTTON))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        before = self.driver.current_url
        btn.click()
        self.wait_with_timeout(10).until(
            lambda d: self.get_inline_errors() or d.current_url != before,
            message="Continue neither moved on nor showed a message",
        )
        return self

    def press_step(self, label: str):
        """Click a stepper button without expecting it to open."""
        self.wait_until_saved()
        btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, W.STEP.format(label=label))))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()
        return self

    def click_previous(self, to_step: str):
        self.wait_until_saved()
        self.click_until(
            W.PREVIOUS_BUTTON,
            lambda d: f"/{to_step}" in d.current_url,
            message=f"Previous never reached the '{to_step}' step",
        )
        return self

    def open_step_url(self, segment: str):
        """Open this record's `segment` step by URL (reload)."""
        base = self.driver.current_url.rsplit("/", 1)[0]
        self.driver.get(f"{base}/{segment}")
        self.wait.until(EC.presence_of_element_located((By.XPATH, W.STEP.format(label=""))))
        self.wait_until_saved()
        return self

    def is_publish_enabled(self) -> bool:
        btn = self.wait.until(
            EC.presence_of_element_located((By.XPATH, W.PUBLISH_BUTTON.format(entity=self.ENTITY)))
        )
        return btn.get_attribute("aria-disabled") != "true" and btn.is_enabled()

    # ─── Navigation and publishing ──────────────────────────────────────────────

    def click_continue(self, to_step: str):
        """Continue to the next step; `to_step` is its URL segment."""
        self.wait_until_saved()
        self.click_until(
            W.CONTINUE_BUTTON,
            lambda d: f"/{to_step}" in d.current_url,
            message=f"Continue never reached the '{to_step}' step",
        )
        return self

    def press_continue(self):
        """Click Continue once, for steps expected to block it."""
        self.wait_until_saved()
        btn = self.wait.until(EC.presence_of_element_located(W.CONTINUE_BUTTON))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        return self

    def press_publish(self):
        """Click Publish once, for drafts expected to be blocked."""
        self.wait_until_saved()
        btn = self.wait.until(EC.presence_of_element_located((By.XPATH, W.PUBLISH_BUTTON.format(entity=self.ENTITY))))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        return self

    def is_text_shown(self, text: str, timeout: int = 10) -> bool:
        return self.is_visible((By.XPATH, W.TEXT.format(text=text)), timeout=timeout)

    def page_text(self, timeout: int = 30) -> str:
        """The step's visible text once it has rendered past the step list."""
        return self.wait_with_timeout(timeout).until(
            lambda d: (t := d.find_element(*W.MAIN).text) and "Previous" in t and t
        )

    STEP_URL = re.compile(r"/(resources|metadata|publish|builder|connect|about|people|content|versions|details)$")

    def wait_for_editor(self):
        """Wait until an editor has settled on one of its steps.

        Opening a draft first lands on the bare `/edit` URL and is then redirected
        to the step it was left at, so the URL alone cannot be read before that.
        """
        self.wait_with_timeout(30).until(
            lambda d: self.STEP_URL.search(d.current_url), message="The editor never settled on a step"
        )
        return self

    def wait_until_synced(self, timeout: int = 30):
        """Wait for a started autosave to finish and the header to read 'All changes saved'.

        The header says 'Saving…' with a single ellipsis character, which the
        three-dot text `wait_until_saved` looks for never matches, so that helper
        returns at once. A save begins as soon as a field changes, so the
        indicator gets a short window to appear before waiting for it to clear.
        """
        saving = (By.XPATH, "//*[normalize-space(text())='Saving…']")
        try:
            WebDriverWait(self.driver, 3, poll_frequency=0.05).until(EC.presence_of_element_located(saving))
        except TimeoutException:
            pass  # already finished, or nothing changed
        self.wait_with_timeout(timeout).until(
            EC.invisibility_of_element_located(saving), message="The editor is still saving"
        )
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located((By.XPATH, "//*[normalize-space(text())='All changes saved']")),
            message="The editor never reported 'All changes saved'",
        )
        return self

    def open_step(self, segment: str):
        """Open another step of the same record by URL (the last path segment) and wait for the save to settle.

        Loading the URL is also how a test reads back what was saved: the page
        is rebuilt from the backend, not from the form's state.
        """
        self.wait_until_synced()
        url = self.driver.current_url.split("?")[0].rsplit("/", 1)[0]
        self.driver.get(f"{url}/{segment}")
        self.wait_with_timeout(30).until(lambda d: f"/{segment}" in d.current_url)
        return self.wait_until_synced()

    def reload(self):
        """Reload the current step from the backend, once every edit has been saved."""
        self.wait_until_synced()
        self.driver.refresh()
        return self.wait_until_synced()

    def click_publish(self, name: str):
        self.wait_until_saved()
        self.click_until(
            (By.XPATH, W.PUBLISH_BUTTON.format(entity=self.ENTITY)),
            lambda d: "/edit/" not in d.current_url,
            message=f"Publish {self.ENTITY} never left the editor",
        )
        self._published_name = name
        return self

    def is_published(self) -> bool:
        """After publishing, the list shows this item's row as Published."""
        try:
            self.wait_with_timeout(30).until(
                EC.visibility_of_element_located(
                    (By.XPATH, W.PUBLISHED_ROW.format(name=self._published_name))
                )
            )
            return True
        except TimeoutException:
            return False
