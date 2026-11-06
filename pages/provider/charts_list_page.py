# pages/provider/charts_list_page.py
import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage
from locators.provider.charts_locators import ChartsLocators


class ChartsListPage(BasePage):
    """
    POM for the 'Add & Manage Charts' page (/dashboard/self/*/charts).
    The chart editor opens inline on the same URL, so creation methods live here too.
    """

    def is_loaded(self, timeout: int = 10) -> bool:
        self.wait_with_timeout(timeout).until(
            EC.visibility_of_element_located(ChartsLocators.ADD_CHART_BTN),
            message="Timed out waiting for the charts list"
        )
        return True

    # ── Chart editor ──────────────────────────────────────────────────────────────

    def click_add_chart(self) -> "ChartsListPage":
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(ChartsLocators.ADD_CHART_BTN),
            message="Timed out waiting for 'Add Chart' button"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(ChartsLocators.DATASET_SEARCH_INPUT),
            message="Timed out waiting for the new chart wizard to open"
        )
        return self

    def select_dataset(self, dataset_name: str) -> "ChartsListPage":
        self.set_react_select_by_text(ChartsLocators.CHART_SELECT_DATASET, dataset_name)
        time.sleep(1)  # resource dropdown populates after dataset is chosen
        return self

    def select_first_dataset_with_resource(self) -> tuple[str, str] | None:
        """Select the first dataset that lists a resource, then that resource.

        Returns (dataset, resource), or None if no dataset on the account has one.
        """
        for dataset in self._option_texts(ChartsLocators.CHART_SELECT_DATASET):
            self.select_dataset(dataset)
            resources = self._option_texts(ChartsLocators.CHART_SELECT_RESOURCE)
            if resources:
                self.select_resource(resources[0])
                return dataset, resources[0]
        return None

    def _option_texts(self, locator) -> list[str]:
        el = self.wait_with_timeout(10).until(EC.presence_of_element_located(locator))
        # Options with an empty value are placeholders like "Select a dataset".
        return [o.text.strip() for o in Select(el).options if o.get_attribute("value")]

    def select_resource(self, resource_name: str) -> "ChartsListPage":
        self.set_react_select_by_text(ChartsLocators.CHART_SELECT_RESOURCE, resource_name)
        return self

    def select_chart_type(self, chart_type: str) -> "ChartsListPage":
        type_map = {
            "BAR":     ChartsLocators.CHART_TYPE_BAR,
            "LINE":    ChartsLocators.CHART_TYPE_LINE,
            "TREEMAP": ChartsLocators.CHART_TYPE_TREEMAP,
        }
        locator = type_map.get(chart_type.upper())
        if not locator:
            raise ValueError(f"Unsupported chart type: {chart_type!r}. Choose from: {list(type_map)}")
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(locator),
            message=f"Timed out waiting for '{chart_type}' chart type button"
        ).click()
        return self

    def click_create_chart(self) -> "ChartsListPage":
        self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(ChartsLocators.CREATE_CHART_BTN),
            message="Timed out waiting for 'Create Chart' button"
        ).click()
        # After creation the app opens the chart detail editor (DATA/CUSTOMIZE tabs)
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(ChartsLocators.CHART_DETAIL_DATA_TAB),
            message="Timed out waiting for chart detail editor to open after creating chart"
        )
        return self

    def close_chart_editor(self) -> "ChartsListPage":
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(ChartsLocators.CLOSE_CHART_EDITOR_BTN),
            message="Timed out waiting for 'Close Editor' button/link"
        )
        self.driver.execute_script("arguments[0].click();", btn)
        # Wait for URL to return to the charts list (no chart ID sub-path)
        self.wait_with_timeout(15).until(
            lambda d: d.current_url.rstrip('/').endswith('/charts'),
            message="Timed out waiting for charts list URL after closing editor"
        )
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(ChartsLocators.SHOWING_CHARTS_HEADING),
            message="Timed out waiting for 'Showing Charts' heading after closing editor"
        )
        return self

    def is_chart_editor_open(self, timeout: int = 5) -> bool:
        return self.is_visible(ChartsLocators.CHART_DETAIL_DATA_TAB, timeout=timeout)

    # ── Getters for assertions ────────────────────────────────────────────────────

    def get_selected_dataset(self) -> str:
        el = self.wait_with_timeout(5).until(
            EC.presence_of_element_located(ChartsLocators.CHART_SELECT_DATASET)
        )
        return Select(el).first_selected_option.text.strip()

    def get_selected_resource(self) -> str:
        el = self.wait_with_timeout(5).until(
            EC.presence_of_element_located(ChartsLocators.CHART_SELECT_RESOURCE)
        )
        return Select(el).first_selected_option.text.strip()

    # ── New chart wizard (Build step) ─────────────────────────────────────────────

    def pick_first_dataset(self) -> str:
        box = self.wait_with_timeout(10).until(EC.presence_of_element_located(ChartsLocators.DATASET_SEARCH_INPUT))
        box.click()
        btn = self.wait_with_timeout(15).until(EC.presence_of_element_located(ChartsLocators.DATASET_RESULT))
        title = btn.text.strip().split("\n")[0]
        self.driver.execute_script("arguments[0].click();", btn)
        return title

    def pick_first_resource(self) -> None:
        combo = self.wait_with_timeout(15).until(EC.presence_of_element_located(ChartsLocators.RESOURCE_COMBOBOX))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", combo)
        combo.click()
        opt = self.wait_with_timeout(10).until(lambda d: next(
            (o for o in d.find_elements(*ChartsLocators.RESOURCE_OPTION) if o.is_displayed()), None))
        opt.click()

    def choose_chart_type(self, name: str) -> None:
        btn = self.wait_with_timeout(10).until(EC.presence_of_element_located(ChartsLocators.chart_type_card(name)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)

    def click_continue(self) -> "ChartsListPage":
        self.wait_for_autosave()
        btn = self.wait_with_timeout(10).until(EC.presence_of_element_located(ChartsLocators.CONTINUE_BTN))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", btn)
        return self

    def is_chart_builder_shown(self, timeout: int = 15) -> bool:
        """Choosing a type reveals the field mapping and Live Preview in place."""
        return self.is_visible(ChartsLocators.LIVE_PREVIEW_HEADING, timeout=timeout)
