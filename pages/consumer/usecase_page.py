# pages/consumer/usecase_page.py
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from locators.consumer.usecase_locators import UseCaseLocators

class UseCasePage(BasePage):
    """Interactions on the Use Cases tab / page."""

    def is_loaded(self) -> bool:
        """Wait for 'Our Use Cases' header to be visible."""
        return self.find(UseCaseLocators.HEADER).is_displayed()

    def has_cards(self):
        """Wait for usecase cards to be present, then return them."""
        return self.finds(UseCaseLocators.CARD)

    # pages/consumer/usecase_page.py

    def download_first_associated_dataset(self, usecase_index: int = 0, dataset_index: int = 0):
        cards = self.driver.find_elements(*UseCaseLocators.UC_FIRST_CARD)
        if len(cards) <= usecase_index:
            return None  # Not enough use cases
        # ... the rest is unchanged
        sector_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"({UseCaseLocators.UC_FIRST_CARD[1]})[{usecase_index + 1}]")
            )
        )
        sector_link.click()
        datasets = self.driver.find_elements(*UseCaseLocators.UC_DATASET_FIRST_CARD)
        if len(datasets) <= dataset_index:
            return None  # Not enough datasets
        dataset_card = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"({UseCaseLocators.UC_DATASET_FIRST_CARD[1]})[{dataset_index + 1}]")
            )
        )
        dataset_card.click()
        download_link = self.wait.until(
            EC.element_to_be_clickable(UseCaseLocators.DOWNLOAD_LINK)
        )
        href = download_link.get_attribute("href")
        status = requests.head(href, allow_redirects=True, timeout=10).status_code
        return (href, status)

    # ── Use case detail page ─────────────────────────────────────────────────

    def open_detail(self, base_url: str, usecase_id):
        """Open /usecases/<id>, wait for the cover title, and return it.

        The title renders for every published use case; the dashboards and
        datasets sections do not, so neither can be the "page loaded" signal.
        """
        self.visit(f"{base_url.rstrip('/')}/usecases/{usecase_id}")
        return self.find(UseCaseLocators.DETAIL_TITLE).text

    def has_dashboards_section(self, timeout: int = 10) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(UseCaseLocators.DETAIL_DASHBOARDS_HEADING)
            )
            return True
        except TimeoutException:
            return False

    def has_datasets_section(self, timeout: int = 10) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(UseCaseLocators.DETAIL_DATASETS_HEADING)
            )
            return True
        except TimeoutException:
            return False

    def dashboards_section_is_gone(self, timeout: int = 10) -> bool:
        """True once "Explore the data" is absent.

        While its query is in flight the section shows its heading over a
        spinner and drops it only if nothing is embeddable, so a snapshot
        taken straight after load proves nothing: wait for it to go.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(UseCaseLocators.DETAIL_DASHBOARDS_HEADING)
            )
            return True
        except TimeoutException:
            return False

    def embedded_dashboards(self):
        """[{title, src}] for each dashboard iframe on the detail page."""
        frames = self.finds(UseCaseLocators.DETAIL_DASHBOARD_IFRAME)
        return [{"title": f.get_attribute("title"), "src": f.get_attribute("src")} for f in frames]

    def dashboards_render_before_datasets(self) -> bool:
        dash = self.find(UseCaseLocators.DETAIL_DASHBOARDS_HEADING)
        datasets = self.find(UseCaseLocators.DETAIL_DATASETS_HEADING)
        return self.driver.execute_script(
            "return !!(arguments[0].compareDocumentPosition(arguments[1]) & Node.DOCUMENT_POSITION_FOLLOWING);",
            dash, datasets,
        )

    # ── cover, story rail, dataset cards, topic chips (DataSpaceFrontend #512) ──

    def cover(self):
        """{back, meta, publisher: {name, kind, href}} read from the cover."""
        publisher = self.find(UseCaseLocators.COVER_PUBLISHER)
        spans = publisher.find_elements(By.XPATH, ".//span/span")
        return {
            "back": self.find(UseCaseLocators.COVER_BACK).get_attribute("href"),
            "meta": self.driver.find_element(*UseCaseLocators.COVER_META).get_attribute("textContent").strip(),
            "publisher": {
                "name": spans[0].get_attribute("textContent").strip(),
                "kind": spans[1].get_attribute("textContent").strip(),
                "href": publisher.get_attribute("href"),
            },
        }

    def contents_links(self):
        """[(label, href)] in the story rail's Contents list."""
        return [(a.get_attribute("textContent").strip(), a.get_attribute("href")) for a in self.finds(UseCaseLocators.CONTENTS_LINKS)]

    def jump_to_story_heading(self, label):
        """Click a Contents link; return (url hash, text of the element with that id) once the hash changes."""
        link = next(a for a in self.finds(UseCaseLocators.CONTENTS_LINKS) if a.get_attribute("textContent").strip() == label)
        target = link.get_attribute("href").split("#", 1)[1]
        link.click()
        self.wait.until(lambda d: d.execute_script("return decodeURIComponent(window.location.hash)") == "#" + target)
        heading = self.driver.find_element(By.ID, target)
        return target, " ".join(heading.get_attribute("textContent").split())

    def contributors(self):
        """[(name, href)] in the story rail's Contributors list."""
        return [
            (a.find_element(By.XPATH, ".//p[1]").get_attribute("textContent").strip(), a.get_attribute("href"))
            for a in self.finds(UseCaseLocators.CONTRIBUTOR_LINKS)
        ]

    def dataset_cards(self):
        """[(href, card text)] for the 'Datasets behind this story' cards."""
        return [(a.get_attribute("href"), a.get_attribute("textContent").strip()) for a in self.finds(UseCaseLocators.DATASET_CARD_LINKS)]

    def open_dataset_card(self, index):
        """Click a dataset card; return the href it pointed at."""
        card = self.finds(UseCaseLocators.DATASET_CARD_LINKS)[index]
        href = card.get_attribute("href")
        card.click()
        return href

    def topic_chips(self, group_title):
        """[(chip text, href)] in a TopicBar group."""
        return [(a.get_attribute("textContent").strip(), a.get_attribute("href")) for a in self.finds(UseCaseLocators.topic_links(group_title))]

    # ── JusticeHub embed (DataSpaceFrontend #492) ───────────────────────────

    def justicehub_theme_preloaded(self, timeout: int = 10) -> dict:
        """Which of the JusticeHub theme preload/preconnect links are present.

        Each check gets its own short wait rather than the page's default 15s,
        so a genuinely-missing link (the pre-#492 behaviour) fails fast instead
        of stalling three times in a row.
        """
        def present(locator):
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
                return True
            except TimeoutException:
                return False

        return {
            "preconnect": present(UseCaseLocators.JUSTICEHUB_PRECONNECT),
            "preload_css": present(UseCaseLocators.JUSTICEHUB_PRELOAD_CSS),
            "preload_logo": present(UseCaseLocators.JUSTICEHUB_PRELOAD_LOGO),
        }

    def justicehub_embed_becomes_ready(self, timeout: int = 12) -> bool:
        """Poll the JusticeHub wrapper's aria-busy until it reads "false".

        Returns False (never raises) if the wrapper never appears or never
        clears aria-busy within `timeout` seconds -- i.e. the spinner never
        actually goes away, which is the failure mode this guards against.
        """
        from selenium.common.exceptions import NoSuchElementException

        def is_ready(driver):
            try:
                el = driver.find_element(*UseCaseLocators.JUSTICEHUB_EMBED_WRAPPER)
            except NoSuchElementException:
                return False
            return el.get_attribute("aria-busy") == "false"

        try:
            WebDriverWait(self.driver, timeout).until(is_ready)
            return True
        except TimeoutException:
            return False
