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
        # 1) click into the combobox input
        combo = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.SECTOR_INPUT)
        ))
        combo.click()

        for val in items:
            # 2) type to filter if needed (sometimes helps)
            combo.clear()
            combo.send_keys(val)

            # 3) click the exact option
            xpath = CreateDatasetLocators.SECTOR_DROPDOWN_ITEM.format(value=val)
            opt = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, xpath)
            ))
            opt.click()

        # 4) close dropdown
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(3)
        return self

    def select_tags(self, items: list[str]):
        # 1) open the tags combobox
        combo = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateDatasetLocators.TAGS_INPUT)
        ))
        combo.click()

        for val in items:
            # 2) optional: filter by typing the tag name
            combo.clear()
            combo.send_keys(val)

            # 3) pick the exact matching option
            xpath = CreateDatasetLocators.TAG_DROPDOWN_ITEM.format(value=val)
            opt = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, xpath)
            ))
            opt.click()

        # 4) close dropdown
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

        # 3) send the absolute file-path to it (this triggers the upload)
        inp.send_keys(path)
        time.sleep(3)
        btn = self.wait.until(EC.presence_of_element_located((By.XPATH, CreateDatasetLocators.BACK_BUTTON)))
        btn.click()

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
        Returns the text of every cell under the “NAME OF RESOURCE” column.
        """
        # wait until at least one row has appeared
        els = self.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, CreateDatasetLocators.RESOURCE_NAME_CELLS)
        ))
        # strip() in case there’s extra whitespace
        return [el.text.strip() for el in els]

    # ─── Publish‐tab getters ─────────────────────────────────────────────────────────────────
    def is_publish_tab_visible(self) -> bool:
        return bool(self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateDatasetLocators.PUBLISH_TAB_CONTAINER))
        ))

    def is_published(self) -> bool:
        # 1) wait for your redirect so you know the mutation has fired
        WebDriverWait(self.driver, 10).until(
            lambda d: "?tab=drafts" in d.current_url
        )
        time.sleep(1)  # give perf logs a moment to fill up

        logs = self.driver.get_log("performance")
        publish_req_id = None

        # 2) find the requestId for the GraphQL call whose payload contains your mutation
        for entry in logs:
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") != "Network.requestWillBeSent":
                continue
            req = msg["params"]["request"]
            # GraphQL POST bodies always have an "operationName"
            # or will literally contain your mutation field
            if req.get("postData") and "publishDataset" in req["postData"]:
                publish_req_id = msg["params"]["requestId"]
                break

        if not publish_req_id:
            return False

        # 3) find exactly that request’s response
        for entry in logs:
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") != "Network.responseReceived":
                continue
            if msg["params"]["requestId"] != publish_req_id:
                continue

            resp = msg["params"]["response"]
            # HTTP 200?
            if resp.get("status") != 200:
                return False

            # pull the actual JSON body via CDP
            body = self.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": publish_req_id}
            )["body"]
            data = json.loads(body)
            status = data.get("data", {}) \
                         .get("publishDataset", {}) \
                         .get("status")
            return status == "PUBLISHED"

        return False

    def get_download_url(self) -> str:
        link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, CreateDatasetLocators.DOWNLOAD_LINK))
        )
        return link.get_attribute("href")