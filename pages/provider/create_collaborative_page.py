# pages/provider/create_collaborative_page.py

from pages.provider.editor_wizard_page import EditorWizardPage
from locators.provider.create_collaborative_locators import CreateCollaborativeLocators as L


class CreateCollaborativePage(EditorWizardPage):
    """Collaborative wizard: About -> People -> Content -> Review & Publish."""

    ENTITY = "Collaborative"

    def edit_collaborative_name(self, name: str):
        self.clear_and_type(L.COLLABORATIVE_NAME_INPUT, name)
        self.wait_for_autosave()
        return self

    def enter_description(self, text: str):
        self.type_into_rich_editor(L.DESCRIPTION_INPUT, text)
        return self

    def enter_platform_url(self, url: str):
        self.clear_and_type(L.PLATFORM_URL_INPUT, url)
        self.wait_for_autosave()
        return self

    def upload_cover_image(self, path_to_file: str):
        return self.upload_image("Cover Image", path_to_file)

    def upload_logo(self, path_to_file: str):
        return self.upload_image("Logo", path_to_file)

    def connect_first_usecase(self) -> str:
        return self.connect_first("Search published Use Cases...", "Use Cases")

    def get_collaborative_name_value(self) -> str:
        return self.find(L.COLLABORATIVE_NAME_INPUT).get_attribute("value")

    def get_description_value(self) -> str:
        return self.find(L.DESCRIPTION_INPUT).text.strip()

    def get_platform_url_value(self) -> str:
        return self.find(L.PLATFORM_URL_INPUT).get_attribute("value")
