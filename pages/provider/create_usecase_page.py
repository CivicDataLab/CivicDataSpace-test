# pages/provider/create_usecase_page.py

import os
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from pages.base_page import BasePage
from locators.provider.create_usecase_locators import CreateUsecaseLocators


class CreateUsecasePage(BasePage):
    """
    Page‐Object Model for the "Create Use Case" modal/flow (step 1 through Publish).
    All methods return `self` where chaining is appropriate, except for `is_published()`.
    """

    def go_to_details_tab(self):
        """
        Click on the "Use Case Details" tab at the top of the wizard.
        """
        self.wait.until(
            EC.element_to_be_clickable(CreateUsecaseLocators.DETAILS_TAB),
            message="Timed out waiting for the 'Use Case Details' tab"
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
        # Try to wait for toast/overlay to disappear, but don't fail if they persist
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass  # Continue anyway

        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.USECASE_SUMMARY_INPUT),
            message="Could not find UseCase summary editor"
        )
        # For Quill editor (contenteditable div), clear using Ctrl+A then type
        fld.click()
        # Ctrl+A works cross-platform (Selenium maps to Cmd+A on Mac)
        fld.send_keys(Keys.CONTROL + 'a')
        fld.send_keys(Keys.DELETE)
        fld.send_keys(text)
        # Send text twice (application-specific behavior)
        fld.send_keys(text)
        return self

    def enter_platform_url(self, url: str):
        # Try to wait for any overlays to disappear, but don't fail if they persist
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass  # Continue anyway

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
        """Select multiple tags using BasePage utility to eliminate duplication"""
        for val in items:
            self.select_combobox_option(CreateUsecaseLocators.TAGS_INPUT, val)
        return self

    def select_sectors(self, items: list[str]):
        """Select multiple sectors using BasePage utility to eliminate duplication"""
        # Try to wait for toast notifications to disappear, but don't fail if they persist
        # (toasts don't block interaction with the form)
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass  # Continue anyway - toasts don't block interaction

        for val in items:
            self.select_combobox_option(CreateUsecaseLocators.SECTOR_INPUT, val)
        return self

    def select_geography(self, value: str):
        import time
        # Wait for geography input to be clickable
        toggle = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.GEOGRAPHY_CONTAINER))
        toggle.click()
        # Type the value to filter the dropdown options
        toggle.send_keys(value)
        time.sleep(2)  # Wait for dropdown to filter
        # Use keyboard to select the first filtered option
        toggle.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        toggle.send_keys(Keys.ENTER)
        time.sleep(0.5)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def select_sdg_goals(self, value: str):
        import time
        toggle = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.SDG_GOALS_CONTAINER))
        toggle.click()
        toggle.send_keys(value)
        time.sleep(2)
        opt = self.wait_with_timeout(30).until(EC.element_to_be_clickable(
            (By.XPATH, f"//div[@role='option' and starts-with(normalize-space(.), '{value}.')]")
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
        # Try to wait for toasts to disappear, but don't fail if they persist
        try:
            self.wait_with_timeout(3).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "toast"))
            )
        except TimeoutException:
            pass  # Continue anyway

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
            message="Could not find 'Completed On' date input"
        )
        fld.clear()
        fld.send_keys(iso_date)
        self.wait.until(lambda d: fld.get_attribute("value") and iso_date in fld.get_attribute("value"))
        return self

    def upload_logo(self, path_to_file: str):
        """
        Triggers logo upload by clicking visible DropZone and sending keys to hidden input.
        Uses BasePage utility method to eliminate code duplication.
        """
        self.scroll_to_element(CreateUsecaseLocators.LOGO_UPLOAD_INPUT)
        return self.upload_file_to_dropzone(path_to_file)

    def get_usecase_name_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.USECASE_NAME_INPUT).get_attribute("value")

    def get_summary_value(self):
        # For contenteditable div, use textContent instead of value attribute
        return self.driver.find_element(*CreateUsecaseLocators.SUMMARY_INPUT).text

    def get_platform_url_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.PLATFORM_URL_INPUT).get_attribute("value")

    def get_selected_tags(self) -> list[str]:
        # time.sleep(2)
        elements = self.driver.find_elements(By.XPATH, CreateUsecaseLocators.SELECTED_TAGS)
        return [el.text.strip() for el in elements]

    def get_selected_sectors(self) -> list[str]:
        # Assuming each selected‐tag appears as a "pill" with text inside
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
        # Use a targeted locator near the SDG Goals label
        sdg_locator = "//label[contains(text(),'SDG')]/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
        try:
            elements = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, sdg_locator))
            )
            return elements[-1].text.strip() if elements else ""
        except TimeoutException:
            elements = self.driver.find_elements(By.XPATH, CreateUsecaseLocators.SELECTED_SDG_GOALS)
            return elements[-1].text.strip() if elements else ""

    def get_started_on_value(self) -> str:
        # Wait for started_on input to be visible
        elt = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.STARTED_ON_VALUE_INPUT)
        )
        return elt.get_attribute("value")

    def get_running_status_value(self) -> str:

        dropdown = Select(self.driver.find_element(*CreateUsecaseLocators.RUNNING_STATUS_SELECT))
        return dropdown.first_selected_option.text

    def get_completed_on_value(self):
        # Wait for completed_on input to be visible
        elt = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.COMPLETED_ON_VALUE_INPUT)
        )
        return elt.get_attribute("value")

    def is_logo_uploaded(self):
        # Wait up to 15s for the action element to show a filename.
        # The server upload is async — React updates the action text only after
        # the upload API call succeeds, so we must poll rather than check once.
        import time

        def _upload_confirmed(d):
            try:
                el = d.find_element(By.XPATH, "//div[contains(@class,'FileUpload-module_Action')]")
                text = el.text.strip()
                return bool(text) and text != "Name of the logo"
            except Exception:
                return False

        try:
            self.wait_with_timeout(15).until(_upload_confirmed)
            return True
        except Exception:
            pass

        # Fallback: check if file input still has the file set (client-side only)
        try:
            input_el = self.driver.find_element(By.XPATH, "//input[@type='file']")
            files_len = self.driver.execute_script("return arguments[0].files.length", input_el)
            return files_len > 0
        except Exception:
            return False

    # ─── "Datasets" Tab ─────────────────────────────────────────────────────────────────────────────────────

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
            message="Could not click 'Submit' on the Datasets tab"
        )
        btn.click()
        return self

    def get_selected_datasets(self):
        selected = self.driver.find_elements(*CreateUsecaseLocators.SELECTED_DATASET_CHECKBOX)
        return [f"Row {i + 1}" for i, _ in enumerate(selected)]

    # ─── "Contributors" Tab ─────────────────────────────────────────────────────────────────────────────────

    def go_to_contributors_tab(self):
        # Wait for Contributors tab to be clickable, then click
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(CreateUsecaseLocators.CONTRIBUTORS_TAB),
            message="Timed out waiting for Contributors tab"
        ).click()
        # Wait for the input field to appear and be ready
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(CreateUsecaseLocators.CONTRIBUTORS_INPUT),
            message="Timed out waiting for 'Add Contributors' input field"
        )
        return self

    def add_contributors(self, names: list[str]):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.CONTRIBUTORS_INPUT),
            message="Could not find 'Add Contributors' input"
        )

        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
            # Wait for async search to complete (element remains visible)
            self.wait.until(EC.visibility_of_element_located(CreateUsecaseLocators.CONTRIBUTORS_INPUT))

        return self

    def add_supporters(self, names: list[str]):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.SUPPORTERS_INPUT),
            message="Could not find 'Add Supporters' input"
        )
        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
        return self

    def add_partners(self, names: list[str]):
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateUsecaseLocators.PARTNERS_INPUT),
            message="Could not find 'Add Partners' input"
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

    # ─── "Publish" Tab ─────────────────────────────────────────────────────────────────────────────────

    def go_to_publish_tab(self):
        """
        Navigate to the Publish tab.
        After click_submit_datasets(), the wizard auto-advances to /dashboards.
        The wizard enforces sequential: DASHBOARDS → CONTRIBUTORS → PUBLISH.
        Use "Next" button to advance through each intermediate step.
        """
        import time
        time.sleep(2)  # Let page stabilize after datasets submission

        # Navigate through wizard until we reach /publish URL
        for _ in range(3):
            if '/publish' in self.driver.current_url:
                break

            # Try clicking "Next" to advance to next wizard step
            try:
                next_btn = self.wait_with_timeout(5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[normalize-space()='Next']")
                    )
                )
                next_btn.click()
                time.sleep(2)
            except TimeoutException:
                # No "Next" button — try clicking PUBLISH tab directly
                try:
                    tab = self.wait_with_timeout(5).until(
                        EC.element_to_be_clickable(CreateUsecaseLocators.PUBLISH_TAB)
                    )
                    self.driver.execute_script("arguments[0].click();", tab)
                    time.sleep(2)
                except TimeoutException:
                    pass
                break

        return self

    def click_publish(self):
        import time

        # On the /publish page the action button has a Button-module class.
        # Try most-specific locators first to avoid accidentally clicking the tab nav button.
        btn = None
        for locator in [
            # Action button with Button-module class (not the tab nav button)
            (By.XPATH, "//button[normalize-space()='Publish' and contains(@class,'Button-module_Button')]"),
            # Fallback: last Publish button in DOM (content buttons appear after tab nav)
            (By.XPATH, "(//button[normalize-space()='Publish'])[last()]"),
        ]:
            try:
                btn = self.wait_with_timeout(5).until(EC.element_to_be_clickable(locator))
                break
            except TimeoutException:
                continue

        if not btn:
            raise TimeoutException("Timed out waiting for Publish action button to become clickable")

        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)

        self.wait_with_timeout(20).until(
            EC.presence_of_element_located(CreateUsecaseLocators.PUBLISHED_MARKER),
            message="Use Case did not show a 'Published' marker"
        )
        return self

    def is_published(self) -> bool:
        try:
            self.wait_with_timeout(10).until(
                EC.presence_of_element_located(CreateUsecaseLocators.PUBLISHED_MARKER),
                message="Published toast not found"
            )
            return True
        except Exception:
            return False
