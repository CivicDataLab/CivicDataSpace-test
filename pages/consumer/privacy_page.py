# pages/consumer/privacy_page.py
from locators.consumer.privacy_locators import PrivacyLocators
from pages.base_page import BasePage

PRIVACY_PATH = "/privacy"


class PrivacyPage(BasePage):
    """Interactions on the privacy policy page (/privacy)."""

    def load(self, base_url: str):
        """
        Navigate to the un-prefixed /privacy path.

        The locale-prefixed /en/privacy 307-redirects here, so /privacy is
        the canonical target.
        """
        self.visit(f"{base_url.rstrip('/')}{PRIVACY_PATH}")
        return self

    def heading_text(self) -> str:
        return self.find(PrivacyLocators.HEADING).text.strip()

    def main_text(self) -> str:
        return self.find(PrivacyLocators.MAIN_CONTENT).text.strip()

    def current_path(self) -> str:
        return self.driver.current_url
