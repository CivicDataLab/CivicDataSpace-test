# pages/provider/create_publication_page.py

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

    # ─── Validation helpers ─────────────────────────────────────────────────────

    def open_editor_step(self, segment: str):
        """Open this draft's `segment` step (files, details, publish) by URL."""
        base = self.driver.current_url.split("?")[0].rsplit("/", 1)[0]
        self.driver.get(f"{base}/{segment}")
        self.wait_with_timeout(30).until(lambda d: f"/{segment}" in d.current_url)
        self.page_text()
        return self

    def attach_file(self, path: str):
        """Hand a local file to the Files step's upload input, as a drop would."""
        self.wait.until(EC.presence_of_element_located(L.FILE_INPUT)).send_keys(path)
        return self

    def try_youtube_video(self, url: str):
        """Enter a YouTube link and press Add video, without expecting it to be accepted."""
        self.click_until(
            L.ADD_YOUTUBE_TOGGLE, EC.visibility_of_element_located(L.YOUTUBE_URL_INPUT),
            message="The YouTube link field never opened",
        )
        self.clear_and_type(L.YOUTUBE_URL_INPUT, url)
        self.driver.execute_script("arguments[0].click();", self.find(L.ADD_VIDEO_BUTTON))
        return self

    def toast_shown(self, text: str, timeout: int = 10) -> bool:
        return self.is_visible((By.XPATH, L.TOAST.format(text=text)), timeout=timeout)

    def file_count(self) -> int:
        """N from the 'Files (N)' heading, or 0 when the list is not shown."""
        found = self.present_now(L.FILES_COUNT)
        return int(re.search(r"Files \((\d+)\)", found[0].text).group(1)) if found else 0

    def accepted_file_types(self) -> str:
        """The upload input's accept list; the drop zone silently ignores anything outside it."""
        return self.wait.until(EC.presence_of_element_located(L.FILE_INPUT)).get_attribute("accept")

    def clear_resource_name(self):
        """Empty the name the way a user would; element.clear() never reaches React's onChange."""
        box = self.wait.until(EC.element_to_be_clickable(L.RESOURCE_NAME_INPUT))
        box.click()
        box.send_keys(Keys.CONTROL, "a")  # Linux (CI); a no-op on macOS
        box.send_keys(Keys.COMMAND, "a")  # macOS; a no-op on Linux
        box.send_keys(Keys.BACKSPACE)
        self.wait.until(lambda d: box.get_attribute("value") == "", message="The resource name never cleared")
        return self

    def type_blank(self, field: str):
        """Put three spaces in the name or description, which clear_and_type would not accept."""
        box = self.wait.until(EC.element_to_be_clickable(L.RESOURCE_NAME_INPUT if field == "name" else L.DESCRIPTION_INPUT))
        box.click()
        box.send_keys(Keys.CONTROL, "a")
        box.send_keys(Keys.COMMAND, "a")
        box.send_keys(Keys.BACKSPACE)
        box.send_keys("   ")
        self.wait.until(lambda d: box.get_attribute("value") == "   ", message=f"The {field} never took the spaces")
        return self.wait_until_synced()

    def enter_external_link(self, url: str):
        self.clear_and_type(L.EXTERNAL_LINK_INPUT, url)
        return self
