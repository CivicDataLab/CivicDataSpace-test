# pages/provider/create_collaborative_page.py

from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.base_page import BasePage
from locators.provider.create_collaborative_locators import CreateCollaborativeLocators as L


class CreateCollaborativePage(BasePage):
    """
    The collaborative editor wizard (DataSpaceFrontend#504):
    About -> People -> Content -> Review & Publish. Every field autosaves.
    """

    # ─── About ──────────────────────────────────────────────────────────────────

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

    def select_sectors(self, items: list[str]):
        for val in items:
            self.select_combobox_option(L.SECTOR_INPUT, val)
        return self

    def select_sdg_goals(self, value: str):
        self.select_combobox_option(L.SDG_GOALS_INPUT, value)
        return self

    def select_tags(self, items: list[str]):
        for val in items:
            self.select_combobox_option(L.TAGS_INPUT, val)
        return self

    def select_geography(self, name: str):
        """Pick the geography called `name`, whatever parent its option shows."""
        self.wait_until_saved()
        combo = self.wait.until(EC.element_to_be_clickable(L.GEOGRAPHY_INPUT))
        combo.click()
        combo.send_keys(name)
        option = (By.XPATH, L.GEOGRAPHY_OPTION.format(listbox=combo.get_attribute("aria-controls"), name=name))
        self.wait_with_timeout(30).until(
            EC.element_to_be_clickable(option), message=f"No geography option for {name!r}"
        ).click()
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()  # the combo re-renders on select
        return self

    def upload_cover_image(self, path_to_file: str):
        return self._upload_image(L.COVER_IMAGE_FILE_INPUT, L.COVER_IMAGE_PREVIEW, path_to_file)

    def upload_logo(self, path_to_file: str):
        return self._upload_image(L.LOGO_FILE_INPUT, L.LOGO_PREVIEW, path_to_file)

    def _upload_image(self, input_locator, preview_locator, path_to_file):
        import os

        self.wait_until_saved()
        field = self.wait.until(EC.presence_of_element_located(input_locator))
        field.send_keys(os.path.abspath(path_to_file))
        self.wait_with_timeout(30).until(
            EC.visibility_of_element_located(preview_locator),
            message=f"No image preview after uploading to {input_locator[1]}",
        )
        self.wait_until_saved()
        return self

    # ─── Content ────────────────────────────────────────────────────────────────

    def connect_first_dataset(self) -> str:
        return self._connect_first(L.DATASET_PICKER_SEARCH, "Datasets")

    def connect_first_usecase(self) -> str:
        return self._connect_first(L.USECASE_PICKER_SEARCH, "Use Cases")

    def _connect_first(self, search_locator, heading) -> str:
        """Open the picker, connect its first result, return that result's title."""
        search = self.wait.until(EC.element_to_be_clickable(search_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search)
        search.click()
        first = self.wait_with_timeout(30).until(
            EC.element_to_be_clickable(L.PICKER_RESULT),
            message=f"The {heading} picker listed no published items",
        )
        title = first.text.split("\n")[0].strip()
        first.click()
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(
                (By.XPATH, L.CONNECTED_TITLE.format(heading=heading, title=title))
            ),
            message=f"'{title}' never showed as connected under {heading}",
        )
        return title

    # ─── Navigation ─────────────────────────────────────────────────────────────

    def click_continue(self, to_step: str):
        """Continue to the next step; `to_step` is its URL segment (people/content/publish)."""
        self.wait_until_saved()
        self.click_until(
            L.CONTINUE_BUTTON,
            lambda d: f"/{to_step}" in d.current_url,
            message=f"Continue never reached the '{to_step}' step",
        )
        return self

    def click_publish(self, name: str):
        self.wait_until_saved()
        self.click_until(
            L.PUBLISH_BUTTON,
            lambda d: "/edit/" not in d.current_url,
            message="Publish Collaborative never left the editor",
        )
        self._published_name = name
        return self

    def is_published(self) -> bool:
        """After publishing, the list shows this collaborative's row as Published."""
        try:
            self.wait_with_timeout(30).until(
                EC.visibility_of_element_located(
                    (By.XPATH, L.PUBLISHED_ROW.format(name=self._published_name))
                )
            )
            return True
        except TimeoutException:
            return False

    # ─── Getters ────────────────────────────────────────────────────────────────

    def get_collaborative_name_value(self) -> str:
        return self.find(L.COLLABORATIVE_NAME_INPUT).get_attribute("value")

    def get_description_value(self) -> str:
        return self.find(L.DESCRIPTION_INPUT).text.strip()

    def get_platform_url_value(self) -> str:
        return self.find(L.PLATFORM_URL_INPUT).get_attribute("value")

    def _chips(self, locator) -> list[str]:
        return [el.get_attribute("title") for el in self.finds(locator)]

    def get_selected_sectors(self) -> list[str]:
        return self._chips(L.SECTOR_CHIPS)

    def get_selected_sdg_goals(self) -> list[str]:
        return self._chips(L.SDG_GOALS_CHIPS)

    def get_selected_tags(self) -> list[str]:
        return self._chips(L.TAG_CHIPS)

    def get_selected_geography(self) -> list[str]:
        return self._chips(L.GEOGRAPHY_CHIPS)
