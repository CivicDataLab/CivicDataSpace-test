# tests/consumer/smoke/test_con_auth_pages.py
#
# Read-only coverage of the Keycloak-hosted sign-in and registration pages
# (DataSpaceKeycloakTheme). Nothing here submits a form or creates an account.
#
# These pages are served by auth.civicdatalab.in and rendered client-side by
# Keycloakify, so they need a real browser - the server HTML is just a
# kcContext blob.
#
# Worth stating why this lives in the CivicDataSpace suite at all: the theme
# repo has no test harness, and these pages are where users actually sign in
# to this app. The privacy links below are the seam - the theme builds them
# with getPrivacyHref() as {baseUrl}/privacy, and tests/consumer/smoke/
# test_con_privacy_policy.py covers the page they point at. Neither side
# previously checked that the link resolves, so the two could drift apart
# with both suites green.

import os

import pytest
import requests

from pages.consumer.keycloak_auth_page import KeycloakLoginPage, KeycloakRegisterPage

pytestmark = [pytest.mark.smoke, pytest.mark.readonly]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

EXPECTED_REGISTER_FIELDS = ("email", "firstName", "lastName")


@pytest.fixture
def login_page(driver):
    return KeycloakLoginPage(driver).load(BASE_URL)


@pytest.fixture
def register_page(driver):
    return KeycloakRegisterPage(driver).load(BASE_URL)


class TestSignInPage:
    def test_google_sign_in_is_offered(self, login_page):
        """Google is a configured IdP on the realm and must reach the user."""
        assert login_page.has_google_button(), (
            "No 'Continue With Google' link on the sign-in page. Google is "
            "configured as an identity provider on the realm, so if this is "
            "missing the theme has stopped rendering social providers and "
            "Google sign-in is silently unavailable."
        )

    def test_google_button_targets_the_broker_endpoint(self, login_page):
        """The button must hit Keycloak's broker, not some other URL."""
        href = login_page.google_login_href() or ""
        assert "/broker/google/login" in href, (
            f"Google button does not point at the broker endpoint: {href!r}"
        )

    def test_registration_is_reachable_from_sign_in(self, login_page):
        """Self-registration is enabled on the realm; the link must be present."""
        assert login_page.has_register_link(), (
            "No registration link on the sign-in page, though the realm has "
            "registrationAllowed=true - new users would have no way in."
        )

    def test_privacy_link_resolves(self, login_page):
        """The privacy link the theme builds must point at a page that exists."""
        hrefs = login_page.privacy_hrefs()
        assert hrefs, "No privacy link on the sign-in page"
        resp = requests.get(hrefs[0], timeout=20)
        assert resp.status_code == 200, (
            f"Privacy link on the sign-in page points at {hrefs[0]!r}, which "
            f"returned HTTP {resp.status_code}. The theme builds this with "
            f"getPrivacyHref(); it has drifted from the app's routes."
        )


class TestRegistrationPage:
    def test_registration_form_renders_expected_fields(self, register_page):
        names = register_page.field_names()
        missing = [f for f in EXPECTED_REGISTER_FIELDS if f not in names]
        assert not missing, f"Registration form is missing {missing}. Present: {names}"

    def test_privacy_consent_checkbox_is_present(self, register_page):
        """The consent checkbox shipped with the privacy policy work."""
        assert register_page.has_terms_checkbox(), (
            "No termsAccepted checkbox on the registration form - users would "
            "be registering without being shown the privacy consent."
        )

    def test_registration_privacy_link_resolves(self, register_page):
        hrefs = register_page.privacy_hrefs()
        assert hrefs, "No privacy link beside the consent checkbox"
        resp = requests.get(hrefs[0], timeout=20)
        assert resp.status_code == 200, (
            f"Privacy link on the registration form points at {hrefs[0]!r}, "
            f"which returned HTTP {resp.status_code}."
        )
