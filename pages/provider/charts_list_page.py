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
            EC.visibility_of_element_located(ChartsLocators.SHOWING_CHARTS_HEADING),
            message="Timed out waiting for 'Showing Charts' heading"
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
            EC.visibility_of_element_located(ChartsLocators.CHARTS_EDITOR_HEADING),
            message="Timed out waiting for Charts Editor to open"
        )
        return self

    def select_dataset(self, dataset_name: str) -> "ChartsListPage":
        self.set_react_select_by_text(ChartsLocators.CHART_SELECT_DATASET, dataset_name)
        time.sleep(1)  # resource dropdown populates after dataset is chosen
        return self

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
