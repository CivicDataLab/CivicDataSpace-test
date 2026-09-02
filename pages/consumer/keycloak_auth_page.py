# pages/consumer/keycloak_auth_page.py
import os

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from locators.consumer.keycloak_auth_locators import (
    KeycloakLoginLocators,
    KeycloakRegisterLocators,
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


def _auth_url(endpoint, app_base_url):
    kc_url, realm, client_id = _kc_settings()
    redirect = f"{app_base_url.rstrip('/')}{CALLBACK_PATH}"
    return (
        f"{kc_url}/realms/{realm}/protocol/openid-connect/{endpoint}"
        f"?client_id={client_id}&response_type=code&scope=openid"
        f"&state=qa&nonce=qa&redirect_uri={redirect}"
    )


class KeycloakLoginPage(BasePage):
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

    def has_register_link(self):
        return self._exists(KeycloakLoginLocators.REGISTER_LINK)

    def privacy_hrefs(self):
        return [e.get_attribute("href") for e in self.driver.find_elements(*KeycloakLoginLocators.PRIVACY_LINK)]

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


class KeycloakRegisterPage(BasePage):
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
