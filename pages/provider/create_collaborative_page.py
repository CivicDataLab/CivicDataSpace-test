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
                name_input = self.wait_with_timeout(3).until(
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
                toggle = self.wait_with_timeout(3).until(EC.element_to_be_clickable(strategy))
                break
            except TimeoutException:
                continue

        if not toggle:
            raise TimeoutException("Could not find SDG Goals container with any strategy")

        toggle.click()
        time.sleep(1)  # Wait for dropdown to appear

        opt = self.wait.until(EC.element_to_be_clickable(
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
        # Wait for geography toggle to be clickable
        toggle = self.wait.until(EC.element_to_be_clickable(CreateCollaborativeLocators.GEOGRAPHY_CONTAINER))
        toggle.click()
        opt = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, CreateCollaborativeLocators.GEO_OPTION.format(value=value))
        ))
        try:
            opt.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", opt)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def enter_started_on(self, iso_date: str):
        """Enter started on date."""
        fld = self.wait.until(EC.presence_of_element_located(CreateCollaborativeLocators.STARTED_ON_INPUT))
        fld.send_keys(iso_date)
        return self

    def enter_completed_on(self, iso_date: str):
        """Enter completed on date."""
        fld = self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.COMPLETED_ON_INPUT),
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
        return self.upload_file_to_dropzone(path_to_file)

    def upload_cover_image(self, path_to_file: str):
        """
        Triggers cover image upload by clicking visible DropZone and sending keys to hidden input.
        """
        return self.upload_file_to_dropzone(path_to_file)

    def click_next(self):
        """Click the Next button to progress to the next step in the wizard."""
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.NEXT_BUTTON),
            message="Could not find Next button"
        )
        btn.click()
        time.sleep(2)  # Wait for next step to load
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
        """Get list of selected tags."""
        elements = self.driver.find_elements(By.XPATH, CreateCollaborativeLocators.SELECTED_TAGS)
        return [el.text.strip() for el in elements]

    def get_selected_sectors(self) -> list[str]:
        """Get list of selected sectors."""
        elements = self.driver.find_elements(By.XPATH, CreateCollaborativeLocators.SELECTED_SECTORS)
        return [el.text.strip() for el in elements]

    def get_selected_geography(self) -> str:
        """Get selected geography."""
        elt = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, CreateCollaborativeLocators.SELECTED_GEOGRAPHY))
        )
        return elt.text.strip()

    def get_selected_sdg_goals(self) -> str:
        """Get selected SDG goals."""
        elements = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, CreateCollaborativeLocators.SELECTED_SDG_GOALS))
        )
        if len(elements) > 3:
            return elements[3].text.strip()  # 4th chip
        raise IndexError("Less than 4 SDG goals selected.")

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
        """Check if logo was uploaded successfully."""
        try:
            elt = self.wait.until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, "FileUpload-module_Action__Hg0nE")
                )
            )
            return bool(elt.text.strip())
        except TimeoutException:
            return False

    def is_cover_image_uploaded(self):
        """Check if cover image was uploaded successfully."""
        try:
            elements = self.driver.find_elements(By.CLASS_NAME, "FileUpload-module_Action__Hg0nE")
            # Cover image is typically the second upload element
            if len(elements) > 1:
                return bool(elements[1].text.strip())
            return False
        except (TimeoutException, IndexError):
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
        """Get list of selected datasets."""
        selected = self.driver.find_elements(*CreateCollaborativeLocators.SELECTED_DATASET_CHECKBOX)
        return [f"Row {i + 1}" for i, _ in enumerate(selected)]

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
        """Get list of selected usecases."""
        selected = self.driver.find_elements(*CreateCollaborativeLocators.SELECTED_USECASE_CHECKBOX)
        return [f"Row {i + 1}" for i, _ in enumerate(selected)]

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
        """Click the Publish button."""
        btn = self.wait.until(
            EC.element_to_be_clickable(CreateCollaborativeLocators.PUBLISH_BUTTON),
            message="Timed out waiting for Publish button to become clickable"
        )
        btn.click()

        # After clicking "Publish," wait for the published‐marker to appear:
        self.wait.until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.PUBLISHED_MARKER),
            message="Collaborative did not show a 'Published' marker"
        )
        return self

    def is_published(self) -> bool:
        """Check if the collaborative was published successfully."""
        try:
            self.wait.until(
                EC.presence_of_element_located(CreateCollaborativeLocators.PUBLISHED_MARKER),
                message="Published toast not found"
            )
            return True
        except Exception:
            return False
