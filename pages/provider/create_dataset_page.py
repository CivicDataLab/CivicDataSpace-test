# pages/provider/create_dataset_page.py

import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.provider.editor_wizard_page import EditorWizardPage
from locators.provider.create_dataset_locators import CreateDatasetLocators as L
from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class CreateDatasetPage(EditorWizardPage):
    """Dataset wizard: Data Files (Prompt Files) -> Metadata -> Review & Publish."""

    ENTITY = "Dataset"

    def is_form_visible(self) -> bool:
        return bool(self.wait.until(EC.visibility_of_element_located((By.XPATH, L.TAB_METADATA))))

    # ---- Steps ----
    def _go_to_step(self, label: str, segment: str):
        self.wait_until_saved()
        self.click_until(
            (By.XPATH, L.STEP_BUTTON.format(label=label)),
            lambda d: f"/edit/{segment}" in d.current_url,
            message=f"The '{label}' step never opened",
        )
        return self

    def go_to_metadata_tab(self):
        self._go_to_step("Metadata", "metadata")
        # The list row is found by this name after publishing.
        self._dataset_name = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, L.TITLE_INPUT))
        ).get_attribute("value")
        return self

    def go_to_datafiles_tab(self):
        return self._go_to_step("Data Files", "resources")

    def go_to_prompt_files_tab(self):
        return self._go_to_step("Prompt Files", "resources")

    def go_to_publish_tab(self):
        return self._go_to_step("Review & Publish", "publish")

    # ---- Metadata ----
    def enter_title(self, title: str):
        self.clear_and_type((By.XPATH, L.TITLE_INPUT), title)
        self.wait_for_autosave()
        return self

    def enter_description(self, text: str):
        self.type_into_rich_editor((By.XPATH, L.DESCRIPTION), text)
        return self

    def select_sectors(self, items: list[str]):
        return self.select_field_options("Sector", items)

    def enter_date_created(self, date_keys: str):
        self.find((By.XPATH, L.DATE_CREATED_INPUT)).send_keys(date_keys)
        self.wait_for_autosave()
        return self

    def enter_source_website(self, url: str):
        self.clear_and_type((By.XPATH, L.SOURCE_INPUT), url)
        self.wait_for_autosave()
        return self

    def select_license(self, license_text: str):
        return self.choose_select_option((By.XPATH, L.LICENSE_SELECT), license_text)

    # Prompt datasets only
    def select_task_type(self, value: str):
        return self.select_field_options("Task Type", [value])

    def select_domain(self, value: str):
        return self.select_field_options("Domain", [value])

    def select_target_languages(self, items: list[str]):
        return self.select_field_options("Target Languages", items)

    def select_target_model_types(self, items: list[str]):
        return self.select_field_options("Target Model Types", items)

    def get_prompt_field_options(self, label: str) -> list[str]:
        """Every option the prompt field labelled `label` offers, e.g. 'Task Type'."""
        select = (By.XPATH, W.SELECT_BY_LABEL.format(label=label))
        if self.driver.find_elements(*select):  # Prompt Format is a button-style select
            return self.get_select_options(select)
        return self.get_combobox_options((By.XPATH, W.FIELD_INPUT.format(label=label)))

    # ---- Files ----
    def _upload(self, path: str) -> str:
        """Upload a file and wait until its card lists it. Returns the file name."""
        filename = os.path.basename(path)
        self.wait.until(EC.presence_of_element_located((By.XPATH, L.DATAFILES_INPUT))).send_keys(path)
        # Wait on this file's card: the list re-renders while uploads land.
        self.wait_with_timeout(60).until(
            EC.presence_of_element_located((By.XPATH, L.UPLOADED_FILE_NAME.format(name=filename))),
            message=f"Timed out waiting for '{filename}' to finish uploading",
        )
        self.wait_until_saved()
        return filename

    def upload_datafile(self, path: str):
        self._upload(path)
        return self

    upload_prompt_file = upload_datafile

    def upload_prompt_file_and_open(self, path: str):
        """Upload a prompt file and open its details sheet (where Prompt Format lives)."""
        filename = self._upload(path)
        self.click_until(
            (By.XPATH, L.VIEW_FILE_BUTTON.format(name=filename)),
            EC.visibility_of_element_located((By.XPATH, L.PROMPT_FILE_SHEET)),
            message=f"'View' never opened the details of '{filename}'",
        )
        return self

    def close_file_details(self):
        # Escape out of a select inside the sheet can already be closing it.
        try:
            self.wait_with_timeout(5).until(
                EC.invisibility_of_element_located((By.XPATH, L.PROMPT_FILE_SHEET))
            )
            return self
        except TimeoutException:
            pass
        self.click_until(
            (By.XPATH, L.SHEET_CLOSE_BUTTON),
            EC.invisibility_of_element_located((By.XPATH, L.PROMPT_FILE_SHEET)),
            message="The file details sheet never closed",
        )
        return self

    # ---- Publish ----
    def is_publish_tab_visible(self) -> bool:
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, L.PUBLISH_DATASET_BUTTON))
        ))

    def click_publish(self):
        return super().click_publish(self._dataset_name)

    # ---- Getters ----
    def get_title_value(self) -> str:
        return self.find((By.XPATH, L.TITLE_INPUT)).get_attribute("value")

    def get_description_value(self) -> str:
        return self.wait.until(EC.visibility_of_element_located((By.XPATH, L.DESCRIPTION))).text.strip()

    def get_selected_sectors(self) -> list[str]:
        return self.selected_chips("Sector")

    def get_selected_geography(self) -> str:
        return ", ".join(self.selected_chips("Geography"))

    def get_selected_task_type(self) -> list[str]:
        return self.selected_chips("Task Type")

    def get_selected_domain(self) -> list[str]:
        return self.selected_chips("Domain")

    def get_selected_target_languages(self) -> list[str]:
        return self.selected_chips("Target Languages")

    def get_selected_target_model_types(self) -> list[str]:
        return self.selected_chips("Target Model Types")

    def get_date_created_value(self) -> str:
        return self.find((By.XPATH, L.DATE_CREATED_INPUT)).get_attribute("value")

    def get_source_website_value(self) -> str:
        return self.find((By.XPATH, L.SOURCE_INPUT)).get_attribute("value").strip()

    def get_selected_license_text(self) -> str:
        return self.find((By.XPATH, L.LICENSE_SELECT)).text.strip()

    def get_uploaded_resource_names(self) -> list[str]:
        return [el.text.strip() for el in self.finds((By.XPATH, L.UPLOADED_FILE_NAMES))]
