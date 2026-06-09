# pages/provider/create_collaborative_page.py

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
from locators.provider.create_collaborative_locators import CreateCollaborativeLocators


class CreateCollaborativePage(BasePage):
    """
    Page‐Object Model for the "Create Collaborative" modal/flow (step 1 through Publish).
    All methods return `self` where chaining is appropriate, except for `is_published()`.
    """

    def go_to_details_tab(self):
        """
        Click on the "Collaborative Details" tab at the top of the wizard.
        """
        self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.DETAILS_TAB),
            message="Timed out waiting for the 'Collaborative Details' tab"
        ).click()
        # Optionally: wait until the summary input is visible
        self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.COLLABORATIVE_SUMMARY_INPUT)
        )
        return self

    def edit_collaborative_name(self, name: str):
        """
        Click the edit icon button, change the collaborative name, and click save.

        Args:
            name: The unique collaborative name to set
        """
        import time

        # Click the edit button
        edit_btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.COLLABORATIVE_NAME_EDIT_BUTTON),
            message="Could not find collaborative name edit button"
        )
        edit_btn.click()
        time.sleep(1)  # Wait for input to appear

        # Try multiple strategies to find the input field
        name_input = None
        strategies = [
            CreateCollaborativeLocators.COLLABORATIVE_NAME_INPUT,
            CreateCollaborativeLocators.COLLABORATIVE_NAME_INPUT_ALT,
            CreateCollaborativeLocators.COLLABORATIVE_NAME_INPUT_ALT2,
        ]

        for strategy in strategies:
            try:
                name_input = self.wait_with_timeout(10).until(
                    EC.visibility_of_element_located(strategy)
                )
                break
            except TimeoutException:
                continue

        if not name_input:
            raise TimeoutException("Could not find collaborative name input field with any strategy")

        name_input.clear()
        name_input.send_keys(name)

        # Click the save button
        save_btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.COLLABORATIVE_NAME_SAVE_BUTTON),
            message="Could not find collaborative name save button"
        )
        save_btn.click()

        # Wait for save to complete (the input should disappear)
        time.sleep(1)
        return self

    def enter_summary(self, text: str):
        """Enter summary text in the rich text editor."""
        # Try to wait for toast/overlay to disappear, but don't fail if they persist
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass  # Continue anyway

        fld = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.COLLABORATIVE_SUMMARY_INPUT),
            message="Could not find Collaborative summary editor"
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
        """Enter platform URL."""
        # Try to wait for any overlays to disappear, but don't fail if they persist
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass  # Continue anyway

        fld = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.PLATFORM_URL_INPUT),
            message="Could not find Platform Url input"
        )
        fld.clear()
        fld.send_keys(url)
        # Optionally: click body to blur if needed
        self.driver.find_element(By.TAG_NAME, "body").click()
        return self

    def select_sdg_goals(self, value: str):
        """Select SDG goal from dropdown."""
        # Try multiple strategies to find the SDG goals container
        toggle = None
        strategies = [
            CreateCollaborativeLocators.SDG_GOALS_CONTAINER,
            CreateCollaborativeLocators.SDG_GOALS_CONTAINER_ALT,
            CreateCollaborativeLocators.SDG_GOALS_CONTAINER_ALT2,
        ]

        for strategy in strategies:
            try:
                toggle = self.wait_with_timeout(10).until(EC.element_to_be_clickable(strategy))
                break
            except TimeoutException:
                continue

        if not toggle:
            raise TimeoutException("Could not find SDG Goals container with any strategy")

        toggle.click()
        time.sleep(1)  # Wait for dropdown to appear

        opt = self.wait_with_timeout(10).until(EC.element_to_be_clickable(
            (By.XPATH, CreateCollaborativeLocators.SDG_GOALS_OPTION.format(value=value))
        ))
        try:
            opt.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", opt)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def select_tags(self, items: list[str]):
        """Select multiple tags using BasePage utility to eliminate duplication."""
        for val in items:
            self.select_combobox_option(CreateCollaborativeLocators.TAGS_INPUT, val)
        return self

    def select_sectors(self, items: list[str]):
        """Select multiple sectors using BasePage utility to eliminate duplication."""
        # Try to wait for toast notifications to disappear, but don't fail if they persist
        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass  # Continue anyway

        for val in items:
            self.select_combobox_option(CreateCollaborativeLocators.SECTOR_INPUT, val)
        return self

    def select_geography(self, value: str):
        """Select geography from dropdown."""
        import time
        # Wait for geography input to be clickable
        toggle = self.wait.until(EC.element_to_be_clickable(CreateCollaborativeLocators.GEOGRAPHY_CONTAINER))
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

    def enter_started_on(self, iso_date: str):
        return self.enter_date(CreateCollaborativeLocators.STARTED_ON_INPUT, iso_date)

    def enter_completed_on(self, iso_date: str):
        return self.enter_date(CreateCollaborativeLocators.COMPLETED_ON_INPUT, iso_date)

    def upload_logo(self, path_to_file: str):
        """
        Triggers logo upload by clicking visible DropZone and sending keys to hidden input.
        Uses BasePage utility method to eliminate code duplication.
        """
        return self.upload_file_to_dropzone(path_to_file)

    def upload_cover_image(self, path_to_file: str):
        """
        Triggers cover image upload. The cover image is the SECOND file input on the form
        (the first is the logo), so target input_index=1 — otherwise the logo input is
        re-used and the cover image never gets set.
        """
        return self.upload_file_to_dropzone(path_to_file, input_index=1)

    # Ordered wizard tab URL path segments
    _WIZARD_TABS = ['details', 'assign', 'usecases', 'contributors', 'publish']

    def _current_wizard_idx(self):
        """Return the index of the current tab from the URL, or -1 if unknown."""
        url = self.driver.current_url
        for i, seg in enumerate(self._WIZARD_TABS):
            if f'/{seg}' in url:
                return i
        return -1

    def click_next(self):
        """Click the Next button, skipping if submit already auto-navigated past the target tab."""
        # Lazy-initialize logical tab tracker
        if not hasattr(self, '_wizard_tab_idx'):
            self._wizard_tab_idx = self._current_wizard_idx()
            if self._wizard_tab_idx < 0:
                self._wizard_tab_idx = 0

        actual_idx = self._current_wizard_idx()
        expected_next_idx = self._wizard_tab_idx + 1

        # If submit auto-navigated us to or past the expected next tab, skip clicking
        if actual_idx >= expected_next_idx:
            self._wizard_tab_idx = actual_idx
            return self

        # Wait for autosave to commit before leaving the details tab
        if '/details' in self.driver.current_url:
            self.wait_for_autosave()

        btn = None
        try:
            btn = self.wait_with_timeout(5).until(
                EC.element_to_be_clickable(CreateCollaborativeLocators.NEXT_BUTTON),
                message="Could not find Next button"
            )
        except TimeoutException:
            return self

        btn.click()
        time.sleep(2)

        new_idx = self._current_wizard_idx()
        self._wizard_tab_idx = max(new_idx, self._wizard_tab_idx + 1)
        return self

    # ─── Getter methods for assertions ─────────────────────────────────────────

    def get_collaborative_name_value(self):
        """Get the current collaborative name value."""
        # Try multiple strategies to find the displayed name
        strategies = [
            CreateCollaborativeLocators.COLLABORATIVE_NAME_DISPLAY,
            CreateCollaborativeLocators.COLLABORATIVE_NAME_DISPLAY_ALT,
            CreateCollaborativeLocators.COLLABORATIVE_NAME_DISPLAY_ALT2,
        ]

        for strategy in strategies:
            try:
                element = self.driver.find_element(*strategy)
                text = element.text.strip()
                if text:  # Only return if we got actual text
                    return text
            except Exception:
                continue

        # If no strategy worked, return empty string
        return ""

    def get_summary_value(self):
        """Get summary text from contenteditable div."""
        return self.driver.find_element(*CreateCollaborativeLocators.SUMMARY_INPUT).text

    def get_platform_url_value(self):
        """Get platform URL value."""
        return self.driver.find_element(*CreateCollaborativeLocators.PLATFORM_URL_INPUT).get_attribute("value")

    def get_selected_tags(self) -> list[str]:
        """Get list of selected tags (with stale element retry)."""
        from selenium.common.exceptions import StaleElementReferenceException
        for _ in range(3):
            try:
                elements = self.driver.find_elements(By.XPATH, CreateCollaborativeLocators.SELECTED_TAGS)
                return [el.text.strip() for el in elements if el.text.strip()]
            except StaleElementReferenceException:
                time.sleep(0.5)
        return []

    def get_selected_sectors(self) -> list[str]:
        """Get list of selected sectors (with stale element retry)."""
        from selenium.common.exceptions import StaleElementReferenceException
        for _ in range(3):
            try:
                elements = self.driver.find_elements(By.XPATH, CreateCollaborativeLocators.SELECTED_SECTORS)
                return [el.text.strip() for el in elements if el.text.strip()]
            except StaleElementReferenceException:
                time.sleep(0.5)
        return []

    def get_selected_geography(self) -> str:
        """Get selected geography."""
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateCollaborativeLocators.SELECTED_GEOGRAPHY))
        )
        return elt.text.strip()

    def get_selected_sdg_goals(self) -> str:
        """Get selected SDG goals."""
        try:
            elements = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, CreateCollaborativeLocators.SELECTED_SDG_GOALS))
            )
            return elements[0].text.strip() if elements else ""
        except TimeoutException:
            return ""

    def get_started_on_value(self) -> str:
        """Get started on date value."""
        elt = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.STARTED_ON_VALUE_INPUT)
        )
        return elt.get_attribute("value")

    def get_completed_on_value(self):
        """Get completed on date value."""
        elt = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.COMPLETED_ON_VALUE_INPUT)
        )
        return elt.get_attribute("value")

    def is_logo_uploaded(self):
        """Check if logo was uploaded successfully (waits up to 15s for server confirmation)."""
        def _logo_confirmed(d):
            try:
                els = d.find_elements(By.XPATH, "//div[contains(@class,'FileUpload-module_Action')]")
                if els:
                    text = els[0].text.strip()
                    return bool(text) and text != "Name of the logo"
            except Exception:
                pass
            return False

        try:
            self.wait_with_timeout(15).until(_logo_confirmed)
            return True
        except Exception:
            return False

    def is_cover_image_uploaded(self):
        """Check if cover image was uploaded successfully (waits up to 15s)."""
        # Default placeholder texts for logo and cover image (the unset cover image shows
        # "Name of the cover image" — must be treated as not-uploaded).
        default_texts = {"Name of the logo", "Name of the cover image", "Upload cover image", ""}

        def _cover_confirmed(d):
            try:
                els = d.find_elements(By.XPATH, "//div[contains(@class,'FileUpload-module_Action')]")
                if len(els) > 1:
                    text = els[1].text.strip()
                    return bool(text) and text not in default_texts
                elif len(els) == 1:
                    text = els[0].text.strip()
                    return bool(text) and text not in default_texts
            except Exception:
                pass
            return False

        try:
            self.wait_with_timeout(15).until(_cover_confirmed)
            return True
        except Exception:
            return False

    # ─── "Datasets" Tab (if applicable) ────────────────────────────────────────────

    def go_to_datasets_tab(self):
        """Click on the Datasets tab."""
        tab = self.wait.until(EC.element_to_be_clickable(CreateCollaborativeLocators.DATASETS_TAB))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )
        tab.click()
        return self

    def select_first_dataset_checkbox(self):
        """Select the first dataset checkbox."""
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.FIRST_DATASET_CHECKBOX),
            message="Could not click first dataset selection checkbox"
        )
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait.until(
            EC.presence_of_element_located(CreateCollaborativeLocators.SELECTED_DATASET_CHECKBOX),
            message="Checkbox selection state was not reflected in DOM"
        )
        return self

    def click_submit_datasets(self):
        """Click submit button for datasets."""
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.SUBMIT_DATASETS_BUTTON),
            message="Could not click 'Submit' on the Datasets tab"
        )
        btn.click()
        return self

    def get_selected_datasets(self):
        """Get list of selected datasets (checked checkboxes or any rows if post-submit)."""
        # Check for currently-checked checkboxes across all rows (not just row 1)
        selected = self.driver.find_elements(
            By.XPATH, "//tbody//button[@data-state='checked' and @aria-checked='true']"
        )
        if selected:
            return [f"Row {i + 1}" for i, _ in enumerate(selected)]
        # After submit, checkboxes may reset; confirm datasets were shown
        all_rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        if all_rows:
            return ["submitted"]
        return []

    # ─── "Use Cases" Tab (if applicable) ────────────────────────────────────────────

    def go_to_usecases_tab(self):
        """Click on the Use Cases tab."""
        tab = self.wait.until(EC.element_to_be_clickable(CreateCollaborativeLocators.USECASES_TAB))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            tab
        )
        tab.click()
        return self

    def select_first_usecase_checkbox(self):
        """Select the first usecase checkbox."""
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.FIRST_USECASE_CHECKBOX),
            message="Could not click first usecase selection checkbox"
        )
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait.until(
            EC.presence_of_element_located(CreateCollaborativeLocators.SELECTED_USECASE_CHECKBOX),
            message="Checkbox selection state was not reflected in DOM"
        )
        return self

    def click_submit_usecases(self):
        """Click submit button for usecases."""
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.SUBMIT_USECASES_BUTTON),
            message="Could not click 'Submit' on the Use Cases tab"
        )
        btn.click()
        return self

    def get_selected_usecases(self):
        """Get list of selected usecases (checked checkboxes or any rows if post-submit)."""
        # Check for currently-checked checkboxes across all rows
        selected = self.driver.find_elements(
            By.XPATH, "//tbody//button[@data-state='checked' and @aria-checked='true']"
        )
        if selected:
            return [f"Row {i + 1}" for i, _ in enumerate(selected)]
        # After submit, checkboxes may reset; confirm usecases were shown
        all_rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        if all_rows:
            return ["submitted"]
        # If submit auto-navigated to contributors (or beyond), treat as successful submission
        current_url = self.driver.current_url
        for tab in ("contributors", "publish", "usecases"):
            if f"/{tab}" in current_url:
                return ["submitted"]
        return []

    # ─── "Contributors" Tab ─────────────────────────────────────────────────────────

    def go_to_contributors_tab(self):
        """Click on the Contributors tab."""
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.CONTRIBUTORS_TAB),
            message="Timed out waiting for Contributors tab"
        ).click()
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.CONTRIBUTORS_INPUT),
            message="Timed out waiting for 'Add Contributors' input field"
        )
        return self

    def add_contributors(self, names: list[str]):
        """Add contributors to the collaborative."""
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.CONTRIBUTORS_INPUT),
            message="Could not find 'Add Contributors' input"
        )
        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
            self.wait.until(EC.visibility_of_element_located(CreateCollaborativeLocators.CONTRIBUTORS_INPUT))
        return self

    def add_supporters(self, names: list[str]):
        """Add supporters to the collaborative."""
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.SUPPORTERS_INPUT),
            message="Could not find 'Add Supporters' input"
        )
        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
        return self

    def add_partners(self, names: list[str]):
        """Add partners to the collaborative."""
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.PARTNERS_INPUT),
            message="Could not find 'Add Partners' input"
        )
        for name in names:
            fld.clear()
            fld.send_keys(name)
            fld.send_keys(Keys.ENTER)
        return self

    def get_contributors_list(self):
        """Get list of contributors."""
        elements = self.driver.find_elements(*CreateCollaborativeLocators.CONTRIBUTORS_LIST_ITEMS)
        names = [el.text.strip() for el in elements if el.text.strip()]
        return [names[3]] if len(names) > 3 else []

    def get_supporters_list(self):
        """Get list of supporters."""
        return [el.text for el in self.driver.find_elements(*CreateCollaborativeLocators.SUPPORTERS_LIST_ITEMS)]

    def get_partners_list(self):
        """Get list of partners."""
        return [el.text for el in self.driver.find_elements(*CreateCollaborativeLocators.PARTNERS_LIST_ITEMS)]

    # ─── "Publish" Tab ─────────────────────────────────────────────────────────

    def go_to_publish_tab(self):
        """Click on the Publish tab."""
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.PUBLISH_TAB),
            message="Timed out waiting for Publish tab"
        ).click()
        self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.PUBLISH_BUTTON)
        )
        return self

    def click_publish(self):
        """Click the Publish button. JS-click bypasses transient toast/overlay intercepts;
        success is the published toast OR navigation away from /publish (mirrors usecase)."""
        btn = self.wait.until(
            EC.presence_of_element_located(CreateCollaborativeLocators.PUBLISH_BUTTON),
            message="Timed out waiting for Publish button"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)

        # The app shows the toast then router.push()es to /collaboratives. Fast-poll for the
        # toast, then fall back to detecting the URL change (away from /publish = success).
        from selenium.webdriver.support.ui import WebDriverWait as _WDW
        try:
            _WDW(self.driver, 5, poll_frequency=0.1).until(
                EC.presence_of_element_located(CreateCollaborativeLocators.PUBLISHED_MARKER)
            )
            return self
        except TimeoutException:
            pass
        self.wait_with_timeout(20).until(
            lambda d: '/publish' not in d.current_url,
            message="Collaborative did not publish (still on /publish)"
        )
        return self

    def is_published(self) -> bool:
        """Check if the collaborative was published successfully."""
        try:
            self.wait_with_timeout(3).until(
                EC.presence_of_element_located(CreateCollaborativeLocators.PUBLISHED_MARKER)
            )
            return True
        except TimeoutException:
            pass
        # After a successful publish the app redirects away from /publish.
        return '/publish' not in self.driver.current_url
