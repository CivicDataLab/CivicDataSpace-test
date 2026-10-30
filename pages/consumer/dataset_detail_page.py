# pages/consumer/dataset_detail_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from locators.consumer.dataset_detail_locators import DatasetDetailLocators as L
from pages.base_page import BasePage

TABS = ("data", "visualisations", "metadata", "connected")


class DatasetDetailPage(BasePage):
    """The public dataset page and its four tabs. Actions and reads only, no assertions."""

    def open(self, base_url, dataset_id, hash=""):
        """Open /datasets/<id>[#hash] and wait until the tabs have rendered."""
        self.visit(f"{base_url.rstrip('/')}/datasets/{dataset_id}{hash}")
        self.find(L.tab("data"))
        return self

    # ── tabs ─────────────────────────────────────────────────────────────────

    def selected_tabs(self):
        """Names of the tabs currently aria-selected."""
        return [t for t in TABS if self.driver.find_element(*L.tab(t)).get_attribute("aria-selected") == "true"]

    def visible_panels(self):
        return [t for t in TABS if self.driver.find_element(*L.panel(t)).is_displayed()]

    def open_tab(self, name):
        self.click(L.tab(name))
        self.wait.until(lambda d: d.find_element(*L.tab(name)).get_attribute("aria-selected") == "true")
        return self

    def wait_for_panel_heading(self, name):
        return self.find(L.PANEL_HEADING[name]).text

    def hash(self):
        return self.driver.execute_script("return window.location.hash")

    # ── data tab ─────────────────────────────────────────────────────────────

    def file_names(self):
        return [b.get_attribute("textContent").strip() for b in self.finds(L.FILE_BUTTONS)]

    def select_file(self, name):
        """Select a file in the tree; return its title, fact line and Download href once shown."""
        button = next(b for b in self.finds(L.FILE_BUTTONS) if b.get_attribute("textContent").strip() == name)
        button.click()
        self.wait.until(lambda d: d.find_element(*L.FILE_TITLE).get_attribute("textContent").strip() == name)
        return {
            "title": self.driver.find_element(*L.FILE_TITLE).get_attribute("textContent").strip(),
            "facts": self.driver.find_element(*L.FILE_FACT_LINE).get_attribute("textContent").strip(),
            "download": self.find(L.FILE_DOWNLOAD).get_attribute("href"),
        }

    # ── visualisations tab ───────────────────────────────────────────────────

    def chart_names(self):
        return [e.get_attribute("textContent").strip() for e in self.finds(L.CHART_NAMES)]

    def has_no_charts_notice(self):
        return self.find(L.NO_CHARTS).is_displayed()

    # ── metadata tab ─────────────────────────────────────────────────────────

    def about_text(self):
        return " ".join(self.find(L.ABOUT_TEXT).get_attribute("textContent").split())

    def info_facts(self):
        """{label: value} for each labelled fact under 'Dataset information' (tags excluded)."""
        self.find(L.PANEL_HEADING["metadata"])
        facts = {}
        for label in self.finds(L.INFO_LABELS):
            value = label.find_elements(By.XPATH, "following-sibling::div[1]")
            if value and label.get_attribute("textContent").strip() != "Tags":
                facts[label.get_attribute("textContent").strip()] = " ".join(value[0].get_attribute("textContent").split())
        return facts

    def tag_links(self):
        """[(label, href)] for the tag chips."""
        return [(a.get_attribute("textContent").strip(), a.get_attribute("href")) for a in self.driver.find_elements(*L.TAG_LINKS)]

    # ── connected tab ────────────────────────────────────────────────────────

    def connected_group_titles(self):
        """['Use cases · 1', ...] once the groups have rendered (the spinner is gone)."""
        return [h.get_attribute("textContent").strip() for h in self.wait.until(EC.presence_of_all_elements_located(L.GROUP_HEADINGS))]

    def connected_card_hrefs(self):
        return [a.get_attribute("href") for a in self.driver.find_elements(*L.CARD_LINKS)]

    def wait_for_connected_cards(self, count):
        self.wait.until(lambda d: len(d.find_elements(*L.CARD_LINKS)) >= count)
        return self.connected_card_hrefs()

    def pressed_filters(self):
        return [b.get_attribute("textContent").strip() for b in self.finds(L.FILTER_BUTTONS) if b.get_attribute("aria-pressed") == "true"]

    def click_filter(self, label):
        next(b for b in self.finds(L.FILTER_BUTTONS) if b.get_attribute("textContent").strip() == label).click()
        self.wait.until(lambda d: self.pressed_filters() == [label])
        return self

    def has_nothing_connected_notice(self):
        return self.find(L.NOTHING_CONNECTED).is_displayed()
