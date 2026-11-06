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
        self.type_into_rich_editor(CreateUsecaseLocators.USECASE_SUMMARY_INPUT, text)
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
        self.wait_until_saved()
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
        self.wait_until_saved()
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
        return self.enter_date(CreateUsecaseLocators.STARTED_ON_INPUT, iso_date)

    def select_running_status(self, status_text: str):
        # Try to wait for toasts to disappear, but don't fail if they persist
        try:
            self.wait_with_timeout(3).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "toast"))
            )
        except TimeoutException:
            pass  # Continue anyway

        # Native <select> autosaves on a React-tracked change; Select.select_by_visible_text
        # fires a DOM change that React's tracked setter ignores, so the choice shows in the
        # DOM but never persists. Set it the React-safe way so autosave commits it.
        self.set_react_select_by_text(CreateUsecaseLocators.RUNNING_STATUS_INPUT, status_text)
        self.wait_for_autosave(trigger_blur=False)
        return self

    def enter_completed_on(self, iso_date: str):
        return self.enter_date(CreateUsecaseLocators.COMPLETED_ON_INPUT, iso_date)

    def upload_logo(self, path_to_file: str):
        """Upload the Builder step's thumbnail through its file input."""
        return self.upload_file_to_dropzone(path_to_file)

    def enter_subtitle(self, text: str):
        fld = self.wait.until(EC.visibility_of_element_located(CreateUsecaseLocators.SUBTITLE_INPUT))
        fld.clear()
        fld.send_keys(text)
        return self

    def get_subtitle_value(self) -> str:
        return self.driver.find_element(*CreateUsecaseLocators.SUBTITLE_INPUT).get_attribute("value")

    def add_text_content(self, text: str):
        """Add a Text block under Content and type into it (the Review step needs one)."""
        btn = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.ADD_CONTENT_BUTTON))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        item = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.ADD_CONTENT_TEXT_ITEM))
        self.driver.execute_script("arguments[0].click();", item)
        self.type_into_rich_editor(CreateUsecaseLocators.SUMMARY_INPUT, text)
        return self

    def click_continue(self):
        """Move to the next wizard step once autosave has settled."""
        self.wait_for_autosave()
        btn = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.CONTINUE_BUTTON))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        return self

    def get_usecase_name_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.USECASE_NAME_INPUT).get_attribute("value")

    def get_summary_value(self):
        # For contenteditable div, use textContent instead of value attribute
        return self.driver.find_element(*CreateUsecaseLocators.SUMMARY_INPUT).text

    def get_platform_url_value(self):
        return self.driver.find_element(*CreateUsecaseLocators.PLATFORM_URL_INPUT).get_attribute("value")

    def _get_pill_texts(self, xpath: str) -> list[str]:
        try:
            elements = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        except TimeoutException:
            return []
        return [el.text.strip() for el in elements if el.text.strip()]

    def get_selected_tags(self) -> list[str]:
        return self._get_pill_texts(CreateUsecaseLocators.SELECTED_TAGS)

    def get_selected_sectors(self) -> list[str]:
        return self._get_pill_texts(CreateUsecaseLocators.SELECTED_SECTORS)

    def get_selected_geography(self) -> str:
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateUsecaseLocators.SELECTED_GEOGRAPHY))
        )
        return elt.text.strip()

    def get_selected_sdg_goals(self) -> str:
        try:
            elements = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, CreateUsecaseLocators.SELECTED_SDG_GOALS))
            )
            return elements[0].text.strip() if elements else ""
        except TimeoutException:
            return ""

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
        """The thumbnail card offers Remove once the upload has landed."""
        try:
            self.wait_with_timeout(20).until(
                EC.visibility_of_element_located(CreateUsecaseLocators.THUMBNAIL_REMOVE_BUTTON)
            )
            return True
        except TimeoutException:
            return False

    # ─── "Datasets" Tab ─────────────────────────────────────────────────────────────────────────────────────

    def select_first_dataset(self) -> str:
        """Pick the first published dataset in the Connect step's search list; return its title."""
        box = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.DATASET_SEARCH_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
        box.click()
        title = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.DATASET_RESULT_TITLE)).text.strip()
        btn = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.DATASET_RESULT_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        return title

    def go_to_datasets_tab(self):
        self.wait_for_autosave()

        tab = self.wait.until(EC.element_to_be_clickable(CreateUsecaseLocators.DATASETS_TAB))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )
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

        # The Publish tab validator reads a React Query cache populated when the
        # usecase was first created (empty). Wizard navigation never refetches, so
        # the "fields missing" error sticks even though autosave persisted the data
        # server-side. Reload once on /publish to force a fresh fetch and clear it.
        if '/publish' in self.driver.current_url:
            self.driver.refresh()
            try:
                self.wait_with_timeout(15).until(
                    EC.element_to_be_clickable(CreateUsecaseLocators.PUBLISH_BUTTON)
                )
            except TimeoutException:
                time.sleep(3)

        return self

    def click_publish(self):
        """Publish from the Review & Publish step."""
        btn = self.wait.until(EC.presence_of_element_located(CreateUsecaseLocators.PUBLISH_BUTTON))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        return self

    def is_published(self) -> bool:
        try:
            self.wait_with_timeout(30).until(lambda d: '/publish' not in d.current_url)
            return True
        except TimeoutException:
            return False
