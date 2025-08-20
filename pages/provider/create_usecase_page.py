# pages/provider/create_usecase_page.py

import os
import time
from time import sleep
from selenium.webdriver.support.ui import Select
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException
from pages.base_page import BasePage
from locators.provider.create_usecase_locators import CreateUsecaseLocators


class CreateUsecasePage(BasePage):
    """
    Page‐Object Model for the “Create Use Case” modal/flow (step 1 through Publish).
    All methods return `self` where chaining is appropriate, except for `is_published()`.
    """

    def go_to_details_tab(self):
        """
        Click on the “Use Case Details” tab at the top of the wizard.
        """
        self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.DETAILS_TAB),
            message="Timed out waiting for the ‘Use Case Details’ tab"
        ).click()
        # Optionally: wait until the summary input is visible
        self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.USECASE_SUMMARY_INPUT)
        )
        return self

    def enter_usecase_name(self, name):
        input_field = self.driver.find_element(By.ID, "usecaseName")  # or By.NAME, By.XPATH, etc.
        input_field.clear()
        input_field.send_keys(str(name))
        return self  # for method chaining

    def enter_summary(self, text: str):
        time.sleep(2)
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.USECASE_SUMMARY_INPUT),
            message="Could not find UseCase summary textarea"
        )
        fld.clear()
        fld.send_keys(text)
        time.sleep(2)
        fld.send_keys(text)
        # fld.send_keys(Keys.TAB)
        return self

    def enter_platform_url(self, url: str):
        time.sleep(3)
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.PLATFORM_URL_INPUT),
            message="Could not find Platform Url input"
        )
        fld.clear()
        fld.send_keys(url)
        # Optionally: click body to blur if needed
        self.driver.find_element(By.TAG_NAME, "body").click()
        return self

    def select_tags(self, items: list[str]):
        # time.sleep(2)
        # 1) open the tags combobox
        combo = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.TAGS_INPUT))
        combo.click()

        for val in items:
            # 2) optional: filter by typing the tag name
            combo.clear()
            combo.send_keys(val)

            # 3) pick the exact matching option
            xpath = CreateUsecaseLocators.TAG_DROPDOWN_ITEM.format(value=val)
            opt = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, xpath)
            ))
            try:
                opt.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", opt)

        # 4) close dropdown
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def select_sectors(self, items: list[str]):
        # 1) click into the combobox input
        time,sleep(3)
        self.wait.until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "toast"))
        )

        combo = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.SECTOR_INPUT))
        combo.click()

        for val in items:
            # 2) type to filter if needed (sometimes helps)
            combo.clear()
            combo.send_keys(val)

            # 3) click the exact option
            xpath = CreateUsecaseLocators.SECTOR_DROPDOWN_ITEM.format(value=val)
            opt = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, xpath)
            ))
            try:
                opt.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", opt)

        # 4) close dropdown
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def select_geography(self, value: str):
        time.sleep(2)
        toggle = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.GEOGRAPHY_CONTAINER))
        toggle.click()
        opt = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateUsecaseLocators.GEO_OPTION.format(value=value))
        ))
        try:
            opt.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", opt)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def select_sdg_goals(self, value: str):
        time.sleep(3)
        toggle = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.SDG_GOALS_CONTAINER))
        toggle.click()
        opt = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateUsecaseLocators.SDG_GOALS_OPTION.format(value=value))
        ))
        try:
            opt.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", opt)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def enter_started_on(self, iso_date: str):
        # 1) locate the date <input>
        fld = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.STARTED_ON_INPUT))
        fld.send_keys(iso_date)
        return self

    def select_running_status(self, status_text: str):
        self.wait.until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "toast"))
        )
        select_el = self.wait.until(
            EC.presence_of_element_located(CreateUsecaseLocators.RUNNING_STATUS_INPUT),
            message="Could not find Running Status <select>"
        )

        from selenium.webdriver.support.ui import Select
        select = Select(select_el)
        select.select_by_visible_text(status_text)
        return self

    def enter_completed_on(self, iso_date: str):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.COMPLETED_ON_INPUT),
            message="Could not find ‘Completed On’ date input"
        )
        fld.clear()
        fld.send_keys(iso_date)
        self.wait.until(lambda d: fld.get_attribute("value") and iso_date in fld.get_attribute("value"))
        return self

    def upload_logo(self, path_to_file: str):
        """
        Triggers logo upload by clicking visible DropZone and sending keys to hidden input.
        """

        # Ensure file is present
        assert os.path.isfile(path_to_file), f"File does not exist: {path_to_file}"

        # First, click anywhere on the DropZone to focus the input (important for React UIs)
        dropzone = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "DropZone-module_DropZone__xD9-6")),
            message="Could not find clickable DropZone"
        )
        dropzone.click()

        # Then get the real <input type="file"> and send keys
        input_el = self.driver.find_element(By.XPATH, "//input[@type='file']")

        self.driver.execute_script("arguments[0].style.display = 'block';", input_el)
        time.sleep(1)  # Give time for UI to stabilize
        input_el.send_keys(path_to_file)

        return self

    def get_usecase_name_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.USECASE_NAME_INPUT).get_attribute("value")

    def get_summary_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.SUMMARY_INPUT).get_attribute("value")

    def get_platform_url_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.PLATFORM_URL_INPUT).get_attribute("value")

    def get_selected_tags(self) -> list[str]:
        # time.sleep(2)
        elements = self.driver.find_elements(By.XPATH, CreateUsecaseLocators.SELECTED_TAGS)
        return [el.text.strip() for el in elements]

    def get_selected_sectors(self) -> list[str]:
        # Assuming each selected‐tag appears as a “pill” with text inside
        elements = self.driver.find_elements(
            By.XPATH, CreateUsecaseLocators.SELECTED_SECTORS
        )
        return [el.text.strip() for el in elements]

    def get_selected_geography(self) -> str:
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateUsecaseLocators.SELECTED_GEOGRAPHY))
        )
        return elt.text.strip()

    def get_selected_sdg_goals(self) -> str:
        time.sleep(2)
        elements = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, CreateUsecaseLocators.SELECTED_SDG_GOALS))
        )
        if len(elements) > 3:
            return elements[3].text.strip()  # 4th chip
        raise IndexError("Less than 4 SDG goals selected.")

    def get_started_on_value(self) -> str:
        time.sleep(2)
        elt = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.STARTED_ON_VALUE_INPUT)
        )
        return elt.get_attribute("value")

    def get_running_status_value(self) -> str:

        dropdown = Select(self.driver.find_element(*CreateUsecaseLocators.RUNNING_STATUS_SELECT))
        return dropdown.first_selected_option.text

    def get_completed_on_value(self):
        time.sleep(2)
        elt = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.COMPLETED_ON_VALUE_INPUT)
        )
        return elt.get_attribute("value")

    def is_logo_uploaded(self):
        try:
            elt = self.wait.until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, "FileUpload-module_Action__Hg0nE")
                )
            )
            return bool(elt.text.strip())
        except:
            return False

    # ─── “Datasets” Tab ─────────────────────────────────────────────────────────────────────────────────────

    def go_to_datasets_tab(self):
        # 1) wait until the tab is clickable
        tab = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.DATASETS_TAB))

        # 2) scroll it into view (centered)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )

        # 3) click and return self for chaining
        tab.click()
        return self

    def select_first_dataset_checkbox(self):
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.FIRST_DATASET_CHECKBOX),
            message="Could not click first dataset selection checkbox"
        )
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for it to reflect selection state
        self.wait.until(
            EC.presence_of_element_located(CreateUsecaseLocators.SELECTED_DATASET_CHECKBOX),
            message="Checkbox selection state was not reflected in DOM"
        )
        return self

    def click_submit_datasets(self):
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.SUBMIT_DATASETS_BUTTON),
            message="Could not click ‘Submit’ on the Datasets tab"
        )
        btn.click()
        return self

    def get_selected_datasets(self):
        selected = self.driver.find_elements(*CreateUsecaseLocators.SELECTED_DATASET_CHECKBOX)
        return [f"Row {i + 1}" for i, _ in enumerate(selected)]

    # ─── “Contributors” Tab ─────────────────────────────────────────────────────────────────────────────────

    def go_to_contributors_tab(self):
        # Click the Contributors tab
        time, sleep(5)
        self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.CONTRIBUTORS_TAB),
            message="Timed out waiting for Contributors tab"
        ).click()
        time,sleep(5)
        # Wait for the input field to appear and be ready
        self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.CONTRIBUTORS_INPUT),
            message="Timed out waiting for 'Add Contributors' input field"
        )
        return self

    def add_contributors(self, names: list[str]):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.CONTRIBUTORS_INPUT),
            message="Could not find ‘Add Contributors’ input"
        )

        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
            time.sleep(0.5)  # slight wait in case async search is involved

        return self

    def add_supporters(self, names: list[str]):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.SUPPORTERS_INPUT),
            message="Could not find ‘Add Supporters’ input"
        )
        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
        return self

    def add_partners(self, names: list[str]):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.PARTNERS_INPUT),
            message="Could not find ‘Add Partners’ input"
        )
        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
        return self

    def get_contributors_list(self):
        elements = self.driver.find_elements(*CreateUsecaseLocators.CONTRIBUTORS_LIST_ITEMS)
        names = [el.text.strip() for el in elements if el.text.strip()]
        # Return only the 4th span if present
        return [names[3]] if len(names) > 3 else []

    def get_supporters_list(self):
        return [el.text for el in self.driver.find_elements(*CreateUsecaseLocators.SUPPORTERS_LIST_ITEMS)]

    def get_partners_list(self):
        return [el.text for el in self.driver.find_elements(*CreateUsecaseLocators.PARTNERS_LIST_ITEMS)]

    # ─── “Publish” Tab ─────────────────────────────────────────────────────────────────────────────────

    def go_to_publish_tab(self):
        time.sleep(3)
        self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.PUBLISH_TAB),
            message="Timed out waiting for Publish tab"
        ).click()
        # Optionally: wait until the Publish button is shown
        self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.PUBLISH_BUTTON)
        )
        return self

    def click_publish(self):
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.PUBLISH_BUTTON),
            message="Timed out waiting for Publish button to become clickable"
        )
        btn.click()

        # After clicking “Publish,” wait for the published‐marker to appear:
        self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.PUBLISHED_MARKER),
            message="Use Case did not show a ‘Published’ marker"
        )
        return self

    def is_published(self) -> bool:
        try:
            self.wait.until(
                EC.presence_of_element_located(CreateUsecaseLocators.PUBLISHED_MARKER),
                message="Published toast not found"
            )
            return True
        except Exception as e:
            print("DEBUG: Toast not found", e)
            # Optional: print all toast texts for diagnosis
            for t in self.driver.find_elements(By.XPATH, "//div[contains(@class,'toast')]"):
                print("Toast visible:", t.text)
            return False
