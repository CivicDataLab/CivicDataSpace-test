# pages/provider/editor_wizard_page.py

import os

from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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
        return [el.get_attribute("title")
                for el in self.finds((By.XPATH, W.FIELD_CHIPS.format(label=label)))]

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
        return title

    def connect_first_dataset(self) -> str:
        return self.connect_first("Search published datasets...", "Datasets")

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
