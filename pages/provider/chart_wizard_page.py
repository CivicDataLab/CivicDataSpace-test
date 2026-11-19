# pages/provider/chart_wizard_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from locators.provider.chart_wizard_locators import ChartWizardLocators as L
from locators.provider.editor_wizard_locators import EditorWizardLocators as W
from pages.provider.editor_wizard_page import EditorWizardPage


class ChartWizardPage(EditorWizardPage):
    """Chart wizard: Build (dataset, file, chart type, fields) -> Review & Publish."""

    def start(self):
        """Press Add Chart on the listing; the wizard opens on its Build step."""
        self.click_until(
            L.ADD_CHART_BUTTON, lambda d: "/charts/new" in d.current_url, message="Add Chart never opened the wizard"
        )
        return self

    def pick_dataset(self, title: str):
        """Search the dataset picker for `title` and add the matching result."""
        search = self.wait.until(EC.element_to_be_clickable((By.XPATH, L.DATASET_SEARCH)))
        search.click()
        search.send_keys(title)
        result = (By.XPATH, W.PICKER_RESULT[1] + f"[.//*[normalize-space()='{title}']]")
        self.click_until(
            result, EC.visibility_of_element_located(L.RESOURCE_SELECT),
            message=f"The picker did not offer the dataset {title!r}",
        )
        return self

    def choose_first_resource(self) -> str:
        name = self.get_select_options(L.RESOURCE_SELECT)[0]
        self.choose_select_option(L.RESOURCE_SELECT, name)
        return name

    def choose_chart_type(self, label: str):
        card = (By.XPATH, L.CHART_TYPE_CARD.format(label=label))
        self.click_until(
            card, EC.visibility_of_element_located(L.EMPTY_FIELD_PICKER),
            message=f"Choosing {label!r} never showed its field pickers",
        )
        return self

    def fill_next_field(self) -> str:
        """Open the first still-empty field picker (X-axis, then the values) and take its first option."""
        picker = self.wait.until(EC.element_to_be_clickable(L.EMPTY_FIELD_PICKER))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", picker)
        picker.click()
        listbox = picker.get_attribute("aria-controls")
        option = self.wait_with_timeout(15).until(
            EC.element_to_be_clickable((By.XPATH, W.LISTBOX_OPTIONS.format(listbox=listbox) + "[1]")),
            message="The field picker listed no fields",
        )
        name = option.text.strip()
        option.click()
        return name

    def continue_to_review(self):
        self.click_continue("publish")
        self.wait.until(EC.visibility_of_element_located(L.CHART_NAME_INPUT))
        return self

    def name_chart(self, name: str):
        self.clear_and_type(L.CHART_NAME_INPUT, name)
        self.wait_until_synced()
        return self

    def publish(self):
        """Press Publish and wait for the 'Chart published' toast."""
        self.click_until(
            L.PUBLISH_BUTTON, EC.visibility_of_element_located(L.PUBLISHED_TOAST),
            message="Publishing the chart never confirmed with 'Chart published'",
        )
        return self
