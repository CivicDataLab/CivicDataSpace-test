# pages/provider/create_ai_model_page.py

from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.provider.editor_wizard_page import EditorWizardPage
from locators.provider.ai_models_locators import AiModelsLocators as L
from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class CreateAiModelPage(EditorWizardPage):
    """AI model wizard: Versions -> Model Information -> Review & Publish."""

    ENTITY = "AI Model"

    # ─── Versions ───────────────────────────────────────────────────────────────

    def add_version(self, name: str, access_name: str, model_id: str, endpoint_url: str):
        """Add a version with one Custom API access method, and save it."""
        self.click_until(L.ADD_VERSION_BTN, EC.visibility_of_element_located(L.VERSION_SHEET),
                         message="Add Version never opened its sheet")
        self.click_until(L.ADD_ACCESS_METHOD_BTN, EC.visibility_of_element_located(L.ACCESS_NAME_INPUT),
                         message="Add Access Method never showed its form")
        self.clear_and_type(L.ACCESS_NAME_INPUT, access_name)
        self.choose_select_option(L.PROVIDER_SELECT, "Custom API")
        self.clear_and_type(L.PROVIDER_MODEL_ID_INPUT, model_id)
        self.clear_and_type(L.API_ENDPOINT_INPUT, endpoint_url)
        self.click_until(L.ADD_ACCESS_METHOD_BTN, EC.invisibility_of_element_located(L.ACCESS_NAME_INPUT),
                         message="The access method was never added to the version")
        self.click_until(L.SAVE_VERSION_BTN, EC.invisibility_of_element_located(L.VERSION_SHEET),
                         message="Save Version never closed the sheet")
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located((By.XPATH, L.SAVED_VERSION.format(name=name))),
            message=f"Version {name} is not listed after saving",
        )
        return self

    # ─── Version sheet, one control at a time ──────────────────────────────────

    def open_version_sheet(self):
        self.click_until(L.ADD_VERSION_BTN, EC.visibility_of_element_located(L.VERSION_SHEET),
                         message="Add Version never opened its sheet")
        return self

    def is_version_sheet_open(self, timeout: int = 5) -> bool:
        return self.is_visible(L.VERSION_NAME_INPUT, timeout=timeout)

    def enter_version_name(self, name: str):
        self.clear_and_type(L.VERSION_NAME_INPUT, name)
        return self

    def open_access_form(self):
        self.click_until(L.ADD_ACCESS_METHOD_BTN, EC.visibility_of_element_located(L.ACCESS_NAME_INPUT),
                         message="Add Access Method never showed its form")
        return self

    def _open_sheet_select(self, trigger_locator):
        trigger = self.wait.until(EC.element_to_be_clickable(trigger_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
        trigger.click()
        return trigger, self.wait_with_timeout(10).until(
            lambda d: [o for o in d.find_elements(*L.VISIBLE_OPTIONS) if o.is_displayed()] or False,
            message="The select listed no options",
        )

    def sheet_select_options(self, trigger_locator) -> list[str]:
        current = self.find(trigger_locator).text.strip()
        _, options = self._open_sheet_select(trigger_locator)
        values = [o.text.strip() for o in options]
        # Esc would close the whole sheet, so close the list by re-picking the current value.
        next((o for o in options if o.text.strip() == current), options[0]).click()
        return values

    def pick_sheet_option(self, trigger_locator, text: str):
        trigger, options = self._open_sheet_select(trigger_locator)
        next(o for o in options if o.text.strip() == text).click()
        self.wait_with_timeout(10).until(lambda d: text in d.find_element(*trigger_locator).text,
                                         message=f"The select never showed {text!r}")
        return self

    def get_sheet_select_value(self, trigger_locator) -> str:
        return self.find(trigger_locator).text.strip()

    def sheet_field_names(self) -> list[str]:
        return [e.get_attribute("name") for e in self.finds(L.SHEET_FIELDS) if e.is_displayed()]

    def sheet_labels(self) -> list[str]:
        return [e.text.strip() for e in self.finds(L.SHEET_LABELS) if e.is_displayed()]

    def fill_sheet_field(self, name: str, value: str):
        self.clear_and_type((By.NAME, name), value)
        self.find((By.NAME, name)).send_keys(Keys.TAB)
        return self

    def sheet_field_validation_message(self, name: str) -> str:
        return self.find((By.NAME, name)).get_attribute("validationMessage")

    def is_access_form_open(self, timeout: int = 3) -> bool:
        return self.is_visible(L.ACCESS_NAME_INPUT, timeout=timeout)

    def press_add_access_method(self):
        self.driver.execute_script("arguments[0].click();", self.find(L.ADD_ACCESS_METHOD_BTN))
        return self

    def press_save_version(self):
        self.driver.execute_script("arguments[0].click();", self.find(L.SAVE_VERSION_BTN))
        return self

    def is_version_saved(self, timeout: int = 15) -> bool:
        """A saved version keeps the sheet open, retitled Edit Version."""
        return self.is_visible(L.EDIT_VERSION_TITLE, timeout=timeout)

    def cancel_version_sheet(self):
        self.click_until(L.SHEET_CANCEL_BTN, EC.invisibility_of_element_located(L.VERSION_SHEET),
                         message="Cancel never closed the version sheet")
        return self

    def listed_versions(self) -> list[str]:
        return [e.text.strip() for e in self.driver.find_elements(*L.VERSION_ROWS) if e.is_displayed()]

    # ─── Model Information ──────────────────────────────────────────────────────

    def go_to_details(self):
        """Open Model Information directly; Continue needs a saved version first."""
        self.driver.get(self.driver.current_url.replace("/versions", "/details"))
        self.wait.until(EC.visibility_of_element_located(L.MODEL_NAME_INPUT))
        return self

    def enter_model_name(self, name: str):
        self.clear_and_type(L.MODEL_NAME_INPUT, name)
        self.wait_for_autosave()
        return self

    def enter_description(self, text: str):
        self.type_into_rich_editor(L.DESCRIPTION_EDITOR, text)
        return self

    def enter_intended_use(self, text: str):
        self.clear_and_type(L.INTENDED_USE_INPUT, text)
        self.wait_for_autosave()
        return self

    def enter_model_website(self, url: str):
        self.clear_and_type(L.MODEL_WEBSITE_INPUT, url)
        self.wait_for_autosave()
        return self

    def select_target_users(self, items: list[str]):
        return self.select_field_options("Target Users", items)

    def select_languages(self, items: list[str]):
        return self.select_field_options("Language Support", items)

    def select_domain(self, text: str):
        return self.select_field_options("Domain", [text], chips=False)

    def get_domain_option_values(self) -> list[str]:
        """Options the Domain combobox lists while empty (the #463 regression left it bare)."""
        combo = self.wait.until(EC.element_to_be_clickable((By.XPATH, W.FIELD_INPUT.format(label="Domain"))))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", combo)
        combo.click()
        listbox = combo.get_attribute("aria-controls")
        options = self.wait_with_timeout(30).until(
            lambda d: d.find_elements(By.XPATH, W.LISTBOX_OPTIONS.format(listbox=listbox)) or False,
            message="The Domain combobox listed no options",
        )
        values = [o.get_attribute("textContent").strip() for o in options]
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return values

    def select_usage_license(self, text: str):
        return self.choose_select_option(L.USAGE_LICENSE_SELECT, text)

    def get_usage_license(self) -> str:
        return self.find(L.USAGE_LICENSE_SELECT).text.strip()

    def get_intended_use_value(self) -> str:
        return self.find(L.INTENDED_USE_INPUT).get_attribute("value")

    def get_model_name_value(self) -> str:
        return self.find(L.MODEL_NAME_INPUT).get_attribute("value")

    def get_description_text(self) -> str:
        return self.find(L.DESCRIPTION_EDITOR).text.strip()
