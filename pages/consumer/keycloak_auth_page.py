# pages/consumer/keycloak_auth_page.py
import os

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from locators.consumer.keycloak_auth_locators import (
    KeycloakErrorLocators,
    KeycloakLoginLocators,
    KeycloakRegisterLocators,
    KeycloakResetLocators,
    KeycloakShellLocators,
)
from pages.base_page import BasePage

# The realm rejects an unregistered redirect_uri with a 400 and renders
# error.ftl instead of the page under test - which looks like a missing
# element rather than a bad URL. This is the app's real NextAuth callback.
CALLBACK_PATH = "/api/auth/callback/keycloak"

VERIFY_EMAIL_MARKER = "VERIFY_EMAIL"
REGISTRATION_PATH = "registrations"


def _kc_settings():
    return (
        os.getenv("KEYCLOAK_URL", "https://auth.civicdatalab.in").rstrip("/"),
        os.getenv("KEYCLOAK_REALM", "DataSpace"),
        os.getenv("KEYCLOAK_CLIENT_ID", "dataspace"),
    )


def _auth_url(endpoint, app_base_url, redirect_uri=None, client_id=None):
    kc_url, realm, default_client = _kc_settings()
    redirect = redirect_uri or f"{app_base_url.rstrip('/')}{CALLBACK_PATH}"
    return (
        f"{kc_url}/realms/{realm}/protocol/openid-connect/{endpoint}"
        f"?client_id={client_id or default_client}&response_type=code&scope=openid"
        f"&state=qa&nonce=qa&redirect_uri={redirect}"
    )


def _squash(text):
    return " ".join((text or "").split())


class _KeycloakPage(BasePage):
    """Helpers for any page rendered inside the theme's CustomTemplate."""

    def heading(self):
        self._await(KeycloakShellLocators.HEADING)
        return self._text(KeycloakShellLocators.HEADING)

    def subtitle(self):
        return self._text(KeycloakShellLocators.SUBTITLE)

    def back_to_home_href(self):
        el = self._find(KeycloakShellLocators.BACK_TO_HOME)
        return el.get_attribute("href") if el else None

    def legal_link_texts(self):
        return [_squash(e.text) for e in self.driver.find_elements(*KeycloakShellLocators.LEGAL_LINKS)]

    def visible_legal_link_texts(self):
        """Privacy/Terms/Legal links a user can actually see at this viewport."""
        return [
            _squash(e.text)
            for e in self.driver.find_elements(*KeycloakShellLocators.ANY_LINK)
            if e.is_displayed() and _squash(e.text).lower() in ("privacy", "terms", "legal")
        ]

    def field_errors(self):
        return [
            _squash(e.text)
            for e in self.driver.find_elements(*KeycloakShellLocators.FIELD_ERROR)
            if _squash(e.text)
        ]

    def alert_text(self):
        return self._text(KeycloakShellLocators.ALERT)

    def card_text(self):
        return self._text(KeycloakShellLocators.CARD)

    def use_mobile_viewport(self, width=390, height=844):
        self.driver.set_window_size(width, height)
        return self

    def has_horizontal_scroll(self):
        return self.driver.execute_script(
            "return document.documentElement.scrollWidth > window.innerWidth"
        )

    def mark_document(self):
        """Tag the live document so a later check can tell if it was replaced.

        A server round trip loads a new document and drops the tag; client-side
        validation leaves it in place.
        """
        self.driver.execute_script("window.__qaMarker = true;")

    def document_was_replaced(self):
        return not self.driver.execute_script("return window.__qaMarker === true;")

    def _wait_ready(self, timeout=20):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def _text(self, locator):
        el = self._find(locator)
        return _squash(el.text) if el else ""

    def _await(self, locator, timeout=20):
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))

    def _exists(self, locator, timeout=15):
        try:
            self._await(locator, timeout)
            return True
        except Exception:
            return False

    def _find(self, locator):
        els = self.driver.find_elements(*locator)
        return els[0] if els else None


class KeycloakLoginPage(_KeycloakPage):
    """The Keycloak sign-in page users reach from the app."""

    def load(self, app_base_url):
        self.driver.get(_auth_url("auth", app_base_url))
        self._await(KeycloakLoginLocators.USERNAME)
        return self

    def has_google_button(self):
        return self._exists(KeycloakLoginLocators.GOOGLE_BROKER_LINK)

    def google_login_href(self):
        el = self._find(KeycloakLoginLocators.GOOGLE_BROKER_LINK)
        return el.get_attribute("href") if el else None

    def google_button_text(self):
        return self._text(KeycloakLoginLocators.GOOGLE_BROKER_LINK)

    def google_button_has_icon(self):
        return self._find(KeycloakLoginLocators.GOOGLE_ICON) is not None

    def has_register_link(self):
        return self._exists(KeycloakLoginLocators.REGISTER_LINK)

    def register_prompt_text(self):
        return self._text(KeycloakLoginLocators.REGISTER_PROMPT)

    def privacy_hrefs(self):
        return [e.get_attribute("href") for e in self.driver.find_elements(*KeycloakLoginLocators.PRIVACY_LINK)]

    def label_texts(self):
        return (
            self._text(KeycloakLoginLocators.USERNAME_LABEL),
            self._text(KeycloakLoginLocators.PASSWORD_LABEL),
        )

    def placeholders(self):
        return (
            self._find(KeycloakLoginLocators.USERNAME).get_attribute("placeholder"),
            self._find(KeycloakLoginLocators.PASSWORD).get_attribute("placeholder"),
        )

    def forgot_link_text(self):
        return self._text(KeycloakLoginLocators.FORGOT_LINK)

    def password_state(self):
        """(input type, toggle aria-label) for the password field."""
        toggle = self._find(KeycloakLoginLocators.PASSWORD_TOGGLE)
        return (
            self._find(KeycloakLoginLocators.PASSWORD).get_attribute("type"),
            toggle.get_attribute("aria-label") if toggle else None,
        )

    def toggle_password(self):
        self._find(KeycloakLoginLocators.PASSWORD_TOGGLE).click()
        return self

    def type_email(self, email):
        el = self._find(KeycloakLoginLocators.USERNAME)
        el.clear()
        el.send_keys(email)
        return self

    def sign_in(self, email, password):
        """Submit credentials. Only ever called with an address that has no account."""
        self.type_email(email)
        self._find(KeycloakLoginLocators.PASSWORD).send_keys(password)
        return self.submit()

    def submit(self):
        self.mark_document()
        self._find(KeycloakLoginLocators.SUBMIT).click()
        self._wait_ready()
        self._await(KeycloakLoginLocators.USERNAME)
        return self

    def go_to_forgot_password(self):
        self._find(KeycloakLoginLocators.FORGOT_LINK).click()
        WebDriverWait(self.driver, 20).until(lambda d: "reset-credentials" in d.current_url)
        return KeycloakResetPage(self.driver).wait_loaded()

    def follow_google(self, timeout=20):
        """Click the Google button and return the host it lands on. Never signs in."""
        kc_host = _kc_settings()[0].split("/")[2]
        self._find(KeycloakLoginLocators.GOOGLE_BROKER_LINK).click()
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.current_url.split("/")[2] != kc_host
            )
        except TimeoutException:
            pass
        return self.driver.current_url.split("/")[2]


class KeycloakResetPage(_KeycloakPage):
    """"Reset your password" - reached from the sign-in page's forgot link."""

    def wait_loaded(self):
        self._await(KeycloakResetLocators.USERNAME)
        return self

    def email_value(self):
        return self._find(KeycloakResetLocators.USERNAME).get_attribute("value")

    def submit_label(self):
        return self._find(KeycloakResetLocators.SUBMIT).get_attribute("value")

    def back_to_sign_in_text(self):
        return self._text(KeycloakResetLocators.BACK_TO_SIGN_IN)

    def request_reset(self, email):
        """Submit the form. Only ever called with an address that has no account."""
        el = self._find(KeycloakResetLocators.USERNAME)
        el.clear()
        if email:
            el.send_keys(email)
        self.mark_document()
        self._find(KeycloakResetLocators.SUBMIT).click()
        self._wait_ready()
        self._await(KeycloakShellLocators.HEADING)
        return self


class KeycloakErrorPage(_KeycloakPage):
    """error.ftl, reached by starting a login the realm refuses."""

    def load_with_redirect(self, app_base_url, redirect_uri):
        self.driver.get(_auth_url("auth", app_base_url, redirect_uri=redirect_uri))
        self._await(KeycloakErrorLocators.TRY_AGAIN)
        return self

    def load_with_client(self, app_base_url, client_id):
        self.driver.get(_auth_url("auth", app_base_url, client_id=client_id))
        self._await(KeycloakErrorLocators.TRY_AGAIN)
        return self


class KeycloakRegisterPage(_KeycloakPage):
    """The Keycloak registration page, including the privacy consent checkbox."""

    def load(self, app_base_url):
        self.driver.get(_auth_url("registrations", app_base_url))
        self._await(KeycloakRegisterLocators.EMAIL)
        return self

    def field_names(self):
        return [
            (el.get_attribute("name") or el.get_attribute("id"))
            for el in self.driver.find_elements("tag name", "input")
            if (el.get_attribute("name") or el.get_attribute("id"))
        ]

    def has_terms_checkbox(self):
        return self._exists(KeycloakRegisterLocators.TERMS_CHECKBOX)

    def privacy_hrefs(self):
        return [e.get_attribute("href") for e in self.driver.find_elements(*KeycloakRegisterLocators.PRIVACY_LINK)]

    def fill(self, email, first_name="QA", last_name="Automation"):
        self._find(KeycloakRegisterLocators.EMAIL).send_keys(email)
        self._find(KeycloakRegisterLocators.FIRST_NAME).send_keys(first_name)
        self._find(KeycloakRegisterLocators.LAST_NAME).send_keys(last_name)
        return self

    def accept_terms(self):
        """Tick the consent box and wait until it has actually registered.

        Clicked via JS: the visible control is a styled label overlaying the
        input, so a plain Selenium click can land on the wrapper instead.

        The wait is not cosmetic. Keycloakify updates React state from the
        click event, and submitting before that lands posts the form without
        consent - which the realm rejects, leaving the test on the form and
        looking like a product bug rather than a race.
        """
        el = self._find(KeycloakRegisterLocators.TERMS_CHECKBOX)
        self.driver.execute_script("arguments[0].click();", el)
        WebDriverWait(self.driver, 10).until(
            lambda d: self._find(KeycloakRegisterLocators.TERMS_CHECKBOX).is_selected()
        )
        return self

    def terms_is_checked(self):
        el = self._find(KeycloakRegisterLocators.TERMS_CHECKBOX)
        return bool(el and el.is_selected())

    def submit(self, timeout=20):
        """Submit and wait for the outcome to settle.

        Waits for the URL to change, which is what a successful registration
        does. A rejected submission keeps the same URL, so the timeout is
        expected there and is swallowed rather than raised - both outcomes are
        legitimate and the caller asserts which one happened.
        """
        url_before = self.driver.current_url
        self._find(KeycloakRegisterLocators.SUBMIT).click()
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.current_url != url_before
            )
        except TimeoutException:
            pass
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return self

    def still_on_registration_form(self):
        """True when the form did not go through - the email field is still there."""
        return REGISTRATION_PATH in self.driver.current_url and self._exists(
            KeycloakRegisterLocators.EMAIL, timeout=5
        )

    def reached_verify_email(self):
        return VERIFY_EMAIL_MARKER in self.driver.current_url

    def body_text(self, timeout=15):
        """Body text, once the page has actually rendered something.

        These pages are React-rendered, so <body> is briefly empty after
        navigation. Reading it straight away returns "" and any assertion
        against the copy fails for reasons that have nothing to do with the
        product.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_element("tag name", "body").text.strip() != ""
            )
        except TimeoutException:
            pass
        return self.driver.find_element("tag name", "body").text

    def sign_in_prompt_text(self):
        return self._text(KeycloakRegisterLocators.SIGN_IN_PROMPT)

    def has_google_button(self):
        return self._exists(KeycloakRegisterLocators.GOOGLE_BROKER_LINK, timeout=5)

    def terms_text(self):
        return self._text(KeycloakRegisterLocators.TERMS_ROW)

    def terms_error_text(self):
        return self._text(KeycloakRegisterLocators.TERMS_ERROR)

    def type_password(self, text):
        """Type into the password field. False when the realm renders none."""
        el = self._find(KeycloakRegisterLocators.PASSWORD)
        if el is None:
            return False
        el.click()
        el.send_keys(text)
        return True

    def submit_without_consent(self):
        """Click Create Account with consent unticked; the theme should block it."""
        self.mark_document()
        self._find(KeycloakRegisterLocators.SUBMIT).click()
        self._wait_ready()
        return self
