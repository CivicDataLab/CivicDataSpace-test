# pages/provider/create_usecase_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.provider.editor_wizard_page import EditorWizardPage
from locators.provider.create_usecase_locators import CreateUsecaseLocators as L


class CreateUsecasePage(EditorWizardPage):
    """Use case wizard: Builder -> Connect -> Review & Publish."""

    ENTITY = "Use Case"

    def enter_title(self, title: str):
        self.clear_and_type(L.TITLE_INPUT, title)
        self.wait_for_autosave()
        return self

    def enter_subtitle(self, subtitle: str):
        self.clear_and_type(L.SUBTITLE_INPUT, subtitle)
        self.wait_for_autosave()
        return self

    def upload_thumbnail(self, path_to_file: str):
        return self.upload_image("Thumbnail", path_to_file)

    def add_text_block(self, text: str):
        self.wait_until_saved()
        self.click_until(
            L.ADD_CONTENT_BUTTON,
            EC.element_to_be_clickable((By.XPATH, L.CONTENT_BLOCK_TYPE.format(kind="Text"))),
            message="Add Content never opened its block menu",
        ).click()
        self.type_into_rich_editor(L.TEXT_BLOCK_EDITOR, text)
        return self

    def get_title_value(self) -> str:
        return self.find(L.TITLE_INPUT).get_attribute("value")

    def get_subtitle_value(self) -> str:
        return self.find(L.SUBTITLE_INPUT).get_attribute("value")

    def get_text_block_value(self) -> str:
        return self.find(L.TEXT_BLOCK_EDITOR).text.strip()
