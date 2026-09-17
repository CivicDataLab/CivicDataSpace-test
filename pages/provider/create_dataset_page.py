# pages/provider/create_dataset_page.py

import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from pages.base_page import BasePage
from locators.provider.create_dataset_locators import CreateDatasetLocators
from pages.provider.dataset_detail_page import DatasetDetailPage
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class CreateDatasetPage(BasePage):
    """POM for the three‐tab Create Dataset editor."""

    def is_form_visible(self) -> bool:
        # “Metadata” tab must be visible
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.TAB_METADATA))
        ))

    # ---- Tab navigation ----
    def go_to_metadata_tab(self):
        self.click((By.XPATH, CreateDatasetLocators.TAB_METADATA))
        self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, CreateDatasetLocators.DESCRIPTION)
        ))
        return self

    def go_to_datafiles_tab(self):
        tab = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.TAB_DATAFILES)
        ))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )
        tab.click()
        return self

    def go_to_prompt_files_tab(self):
        tab = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.TAB_PROMPT_FILES)
        ))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )
        tab.click()
        return self

    def go_to_publish_tab(self):
        self.click((By.XPATH, CreateDatasetLocators.TAB_PUBLISH))
        self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, CreateDatasetLocators.PUBLISH_REVIEW_TEXT)
        ))
        return self

    # ---- Metadata entry ----
    def enter_description(self, text: str):
        fld = self.find((By.XPATH, CreateDatasetLocators.DESCRIPTION))
        fld.click()
        fld.send_keys(Keys.CONTROL + 'a')
        fld.send_keys(Keys.DELETE)
        fld.send_keys(text)
        return self

    def select_sectors(self, items: list[str]):
        """Select multiple sectors using BasePage utility to eliminate duplication"""
        for val in items:
            self.select_combobox_option((By.XPATH, CreateDatasetLocators.SECTOR_INPUT), val)
        # Wait for any toast notifications to disappear, but don't fail if they persist
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=5)
        except TimeoutException:
            pass  # Continue anyway - toasts don't block interaction
        return self

    def select_tags(self, items: list[str]):
        """Select multiple tags using BasePage utility to eliminate duplication"""
        for val in items:
            self.select_combobox_option((By.XPATH, CreateDatasetLocators.TAGS_INPUT), val)
        return self

    def select_geography(self, value: str):
        self.wait_until_saved()
        import time

        toggle = self.wait_with_timeout(10).until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.GEOGRAPHY_CONTAINER)
        ))
        toggle.click()

        # Type the value to filter the dropdown options
        toggle.send_keys(value)
        time.sleep(2)

        # Use keyboard to select the first filtered option
        toggle.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        toggle.send_keys(Keys.ENTER)
        time.sleep(0.5)

        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def enter_date_created(self, iso_date: str):

        # 1) locate the date <input>
        fld = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, CreateDatasetLocators.DATE_CREATED_INPUT)
        ))
        fld.send_keys(iso_date)
        return self

    def enter_source_website(self, url: str):
        fld = self.find((By.XPATH, CreateDatasetLocators.SOURCE_INPUT))
        fld.clear()
        fld.send_keys(url)
        return self

    def select_license(self, license_text: str):
        """
        Picks the desired license from the native <select>.
        """
        # 1) wait for the <select> to be present
        sel_elem = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, CreateDatasetLocators.LICENSE_SELECT)
        ))

        # 2) wrap it in the Select helper and choose by visible text
        sel = Select(sel_elem)
        sel.select_by_visible_text(license_text)

        return self

    # ---- Prompt Dataset Metadata fields ----
    def _scroll_to_locator(self, locator):
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def select_task_type(self, value: str):
        loc = (By.XPATH, CreateDatasetLocators.TASK_TYPE_INPUT)
        self._scroll_to_locator(loc)
        self.select_combobox_option(loc, value)
        return self

    def select_domain(self, value: str):
        loc = (By.XPATH, CreateDatasetLocators.DOMAIN_INPUT)
        self._scroll_to_locator(loc)
        self.select_combobox_option(loc, value)
        return self

    def select_target_languages(self, items: list[str]):
        loc = (By.XPATH, CreateDatasetLocators.TARGET_LANGUAGES_INPUT)
        self._scroll_to_locator(loc)
        for val in items:
            self.select_combobox_option(loc, val)
        return self

    def select_target_model_types(self, items: list[str]):
        loc = (By.XPATH, CreateDatasetLocators.TARGET_MODEL_TYPES_INPUT)
        self._scroll_to_locator(loc)
        for val in items:
            self.select_combobox_option(loc, val)
        return self

    def get_selected_task_type(self) -> list[str]:
        els = self.driver.find_elements(By.XPATH, CreateDatasetLocators.TASK_TYPE_SELECTED_PILL)
        return [el.text.strip() for el in els]

    def get_selected_domain(self) -> list[str]:
        els = self.driver.find_elements(By.XPATH, CreateDatasetLocators.DOMAIN_SELECTED_PILL)
        return [el.text.strip() for el in els]

    def get_selected_target_languages(self) -> list[str]:
        els = self.driver.find_elements(By.XPATH, CreateDatasetLocators.TARGET_LANGUAGES_SELECTED_PILL)
        return [el.text.strip() for el in els]

    def get_selected_target_model_types(self) -> list[str]:
        els = self.driver.find_elements(By.XPATH, CreateDatasetLocators.TARGET_MODEL_TYPES_SELECTED_PILL)
        return [el.text.strip() for el in els]

    # ---- File upload ----
    def _upload_and_return_to_list(self, path: str, go_to_tab) -> None:
        """Upload a file, wait until it has really landed, then return to the file list.

        When an upload finishes the app opens that file's edit view. Clicking back
        as soon as the back arrow appears could land mid-upload; the completed
        upload then reopened the edit view, and the resource-name getter fell back
        to its schema table and returned column names (test_prv_002b).
        """
        import os

        filename = os.path.basename(path)
        inp = self.wait.until(EC.presence_of_element_located((By.XPATH, CreateDatasetLocators.DATAFILES_INPUT)))
        inp.send_keys(path)

        # The edit view for this upload names the file once the upload is done.
        self.wait_with_timeout(60).until(
            EC.presence_of_element_located((By.XPATH, f"//*[normalize-space(text())='{filename}']")),
            message=f"Timed out waiting for '{filename}' to finish uploading",
        )
        self.wait_until_saved()
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.BACK_BUTTON))
        ).click()

        go_to_tab()
        self.wait_with_timeout(30).until(
            lambda d: any(
                el.text.strip() == filename
                for el in d.find_elements(By.XPATH, CreateDatasetLocators.RESOURCE_NAME_CELLS)
            ),
            message=f"Timed out waiting for '{filename}' in the uploaded file list",
        )

    def upload_datafile(self, path: str):
        self._upload_and_return_to_list(path, self.go_to_datafiles_tab)
        return self

    def upload_prompt_file(self, path: str):
        self._upload_and_return_to_list(path, self.go_to_prompt_files_tab)
        return self

    # ---- Final publish ----
    def click_publish(self) -> DatasetDetailPage:
        self.click((By.XPATH, CreateDatasetLocators.PUBLISH_BUTTON))
        return DatasetDetailPage(self.driver)

    # ----Getter functions----

    def get_description_value(self) -> str:
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.DESCRIPTION))
        )
        return elt.text.strip()

    def get_selected_sectors(self) -> list[str]:
        # Assuming each selected‐tag appears as a “pill” with text inside
        elements = self.driver.find_elements(
            By.XPATH, CreateDatasetLocators.SECTOR_SELECTED_PILL
        )
        return [el.text.strip() for el in elements]

    def get_selected_tags(self) -> list[str]:
        elements = self.driver.find_elements(
            By.XPATH, CreateDatasetLocators.TAG_SELECTED_PILL
        )
        return [el.text.strip() for el in elements]

    def get_selected_geography(self) -> str:
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.GEOGRAPHY_SELECTED_PILL))
        )
        return elt.text.strip()

    def get_date_created_value(self) -> str:
        """
        Returns the “value” attribute of the <input type='date'> field,
        which should be in YYYY-MM-DD format.
        """
        inp = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.GET_DATE_CREATED))
        )
        return inp.get_attribute("value")

    def get_source_website_value(self) -> str:
        inp = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.SOURCE_WEBSITE_INPUT))
        )
        return inp.get_attribute("value").strip()

    def get_selected_license_text(self) -> str:
        # If LICENSE_CONTAINER is the dropdown, maybe the current selection is inside a <span> there.
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.LICENSE_SELECTED_TEXT))
        )
        return elt.text.strip()

    def get_uploaded_resource_names(self) -> list[str]:
        """
        Returns the text of every cell under the "NAME OF RESOURCE" column.
        """
        # wait until at least one row has appeared
        # Try multiple locator strategies in case the table structure changed
        try:
            els = self.wait_with_timeout(10).until(EC.presence_of_all_elements_located(
                (By.XPATH, CreateDatasetLocators.RESOURCE_NAME_CELLS)
            ))
        except:
            # Try alternative: any table row's first cell
            try:
                els = self.wait_with_timeout(5).until(EC.presence_of_all_elements_located(
                    (By.XPATH, "//table//tbody//tr//td[1]")
                ))
            except:
                # Try another alternative: look for file names anywhere in the data files section
                els = self.wait_with_timeout(5).until(EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'datafile') or contains(@class, 'resource')]//span | //div[contains(@class, 'datafile') or contains(@class, 'resource')]//div")
                ))

        # strip() in case there's extra whitespace
        return [el.text.strip() for el in els if el.text.strip()]

    # ─── Publish‐tab getters ─────────────────────────────────────────────────────────────────
    def is_publish_tab_visible(self) -> bool:
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.PUBLISH_TAB_CONTAINER))
        ))

    def is_published(self) -> bool:
        """
        Check if the dataset has been published by navigating to the Published tab.

        After clicking Publish, the page redirects to the drafts tab. We then need to
        click on the "Published" tab to verify the dataset appears there.

        Returns:
            True if we can successfully navigate to the Published tab, False otherwise
        """
        # Wait for URL to change to drafts tab (confirms redirect after publish)
        self.wait_with_timeout(10).until(
            lambda d: "?tab=drafts" in d.current_url
        )

        # Wait a moment for the UI to update after redirect
        import time
        time.sleep(2)

        # Click on the "Published" tab to verify dataset is there
        try:
            published_tab = self.wait_with_timeout(10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[normalize-space()='Published']")
                )
            )
            published_tab.click()

            # Wait for the Published tab to load
            time.sleep(2)

            # Verify URL changed to published tab
            self.wait_with_timeout(10).until(
                lambda d: "?tab=published" in d.current_url.lower()
            )

            return True
        except TimeoutException:
            # If we can't navigate to published tab or it times out
            return False

    def get_download_url(self) -> str:
        link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DOWNLOAD_LINK))
        )
        return link.get_attribute("href")