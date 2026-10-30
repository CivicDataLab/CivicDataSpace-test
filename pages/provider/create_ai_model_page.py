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
        return self.select_field_options("Domain", [text])

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

    def get_model_name_value(self) -> str:
        return self.find(L.MODEL_NAME_INPUT).get_attribute("value")

    def get_description_text(self) -> str:
        return self.find(L.DESCRIPTION_EDITOR).text.strip()
