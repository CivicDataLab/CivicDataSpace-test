# pages/provider/create_publication_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from locators.provider.create_publication_locators import CreatePublicationLocators as L
from locators.provider.editor_wizard_locators import EditorWizardLocators as W
from pages.provider.editor_wizard_page import EditorWizardPage


class CreatePublicationPage(EditorWizardPage):
    """Publication wizard: Files -> Details -> Review & Publish."""

    ENTITY = "Publication"

    def start(self):
        """Press Create Publication on the listing; it creates a draft and opens Files."""
        self.click_until(
            L.CREATE_BUTTON, lambda d: d.current_url.endswith("/files"), message="Create Publication never opened the editor"
        )
        return self

    def add_youtube_video(self, url: str):
        self.click_until(
            L.ADD_YOUTUBE_TOGGLE, EC.visibility_of_element_located(L.YOUTUBE_URL_INPUT),
            message="The YouTube link field never opened",
        )
        self.clear_and_type(L.YOUTUBE_URL_INPUT, url)
        self.click_until(
            L.ADD_VIDEO_BUTTON, EC.visibility_of_element_located(L.FILES_READY),
            message="The YouTube video was never added to the file list",
        )
        return self

    def enter_resource_name(self, name: str):
        self.clear_and_type(L.RESOURCE_NAME_INPUT, name)
        self.wait_until_synced()
        return self

    def enter_description(self, text: str):
        self.clear_and_type(L.DESCRIPTION_INPUT, text)
        self.wait_until_synced()
        return self

    def enter_date(self, iso_date: str):
        return super().enter_date(L.DATE_INPUT, iso_date)

    def choose_resource_type(self) -> str:
        """Pick the first resource type the backend offers."""
        name = self.get_select_options(L.RESOURCE_TYPE_SELECT)[0]
        self.choose_select_option(L.RESOURCE_TYPE_SELECT, name)
        return name

    def select_geography(self, name: str):
        """Pick a geography; this wizard lists them by plain name, unlike the others ("India (Asia Pacific)")."""
        return self.select_field_options("Geography", [name])

    def add_contributor(self, name: str):
        """Search the contributor picker for `name` and add the first match."""
        search = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, W.PICKER_SEARCH.format(placeholder="Search contributors...")))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search)
        search.click()
        search.send_keys(name)
        self.click_until(
            W.PICKER_RESULT, EC.invisibility_of_element_located(L.NO_CONTRIBUTORS),
            message=f"The contributor picker offered nobody called {name!r}",
        )
        return self
