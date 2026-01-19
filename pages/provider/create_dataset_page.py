# pages/provider/create_dataset_page.py

import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
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
        # 1) wait until the tab is clickable
        tab = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.TAB_DATAFILES)
        ))

        # 2) scroll it into view (centered)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )

        # 3) click and return self for chaining
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
        fld.clear()
        fld.send_keys(text)
        return self

    def select_sectors(self, items: list[str]):
        """Select multiple sectors using BasePage utility to eliminate duplication"""
        for val in items:
            self.select_combobox_option((By.XPATH, CreateDatasetLocators.SECTOR_INPUT), val)
        # Wait for any toast notifications to disappear after selections
        self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=5)
        return self

    def select_tags(self, items: list[str]):
        """Select multiple tags using BasePage utility to eliminate duplication"""
        for val in items:
            self.select_combobox_option((By.XPATH, CreateDatasetLocators.TAGS_INPUT), val)
        return self

    def select_geography(self, value: str):
        toggle = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.GEOGRAPHY_CONTAINER)
        ))
        toggle.click()
        opt = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.GEO_OPTION.format(value=value))
        ))
        opt.click()
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

    # ---- File upload ----
    def upload_datafile(self, path: str):

        # locate the file‐input directly
        inp = self.wait.until(EC.presence_of_element_located((By.XPATH, CreateDatasetLocators.DATAFILES_INPUT)))

        # send the absolute file-path to it (this triggers the upload)
        print(f"[DEBUG] Uploading file: {path}")
        inp.send_keys(path)

        # Wait for back button to be present (indicates upload initiated)
        btn = self.wait_with_timeout(10).until(
            EC.presence_of_element_located((By.XPATH, CreateDatasetLocators.BACK_BUTTON))
        )
        print("[DEBUG] Back button found, clicking...")
        btn.click()

        # Wait for the uploaded file to appear in the resource list
        # Give it a moment to process and display
        import time
        time.sleep(3)  # Increased wait time

        print(f"[DEBUG] Current URL after upload: {self.driver.current_url}")

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
        return elt.get_attribute("value").strip()

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
        result = [el.text.strip() for el in els if el.text.strip()]
        print(f"[DEBUG] Found uploaded resources: {result}")
        return result

    # ─── Publish‐tab getters ─────────────────────────────────────────────────────────────────
    def is_publish_tab_visible(self) -> bool:
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.PUBLISH_TAB_CONTAINER))
        ))

    def is_published(self) -> bool:
        """
        Check if the dataset has been published by looking for the "Published" status badge.

        After clicking Publish, the page redirects to the drafts tab where the newly
        published dataset should have a "Published" status badge visible.

        Returns:
            True if the "Published" status badge is found, False otherwise
        """
        # Wait for URL to change to drafts tab (confirms redirect after publish)
        self.wait_with_timeout(10).until(
            lambda d: "?tab=drafts" in d.current_url
        )

        # Wait a moment for the UI to update after redirect
        import time
        time.sleep(1)

        # Check for the "Published" status badge
        try:
            self.wait_with_timeout(10).until(
                EC.presence_of_element_located(
                    (By.XPATH, CreateDatasetLocators.PUBLISHED_STATUS_BADGE)
                )
            )
            return True
        except TimeoutException:
            # If badge not found within timeout, dataset is not published
            return False

    def get_download_url(self) -> str:
        link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DOWNLOAD_LINK))
        )
        return link.get_attribute("href")