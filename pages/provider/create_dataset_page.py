from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage
from locators.provider.create_dataset_locators import CreateDatasetLocators
from pages.provider.dataset_detail_page import DatasetDetailPage

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
        self.click((By.XPATH, CreateDatasetLocators.TAB_DATAFILES))

        # wait for the real <input type="file"> to be present
        self.wait.until(EC.presence_of_element_located((By.XPATH, CreateDatasetLocators.DATAFILES_INPUT)))
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
        toggle = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.SECTORS_CONTAINER)
        ))
        toggle.click()
        for val in items:
            opt = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, CreateDatasetLocators.SECTOR_OPTION.format(value=val))
            ))
            opt.click()
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def select_tags(self, items: list[str]):
        toggle = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.TAGS_CONTAINER)
        ))
        toggle.click()
        for val in items:
            opt = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, CreateDatasetLocators.TAG_OPTION.format(value=val))
            ))
            opt.click()
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
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

    def enter_date_created(self, iso_date: str, timeout: int = 10):

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

        # 3) send the absolute file-path to it (this triggers the upload)
        inp.send_keys(path)

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

    def get_uploaded_filenames(self) -> list[str]:
        # Suppose after uploading a file, each uploaded resource row has a <td> with the filename
        elements = self.driver.find_elements(
            By.XPATH, CreateDatasetLocators.UPLOADED_FILES_NAME_CELLS
        )
        return [el.text.strip() for el in elements]

    # ─── Publish‐tab getters ─────────────────────────────────────────────────────────────────
    def is_publish_tab_visible(self) -> bool:
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.PUBLISH_TAB_CONTAINER))
        ))

    def is_published(self) -> bool:
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.PUBLISHED_STATUS_BADGE))
        ))

    def get_download_url(self) -> str:
        link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DOWNLOAD_LINK))
        )
        return link.get_attribute("href")