# tests/consumer/smoke/test_con_auth_pages.py
#
# The Keycloak-hosted auth pages (DataSpaceKeycloakTheme) checked against the
# sign-in / sign-up design. Runs against production auth.civicdatalab.in after
# every theme deploy and every 6h, so everything here must stay read-only:
#
#   - No account is created and no real account is touched.
#   - The only submissions are a failed sign-in and a password-reset request,
#     both for a random @example.invalid address that has no account. Keycloak
#     writes nothing for an unknown user and sends no email.
#   - The register form is only ever submitted with consent unticked, which the
#     theme blocks in the browser before anything reaches the server.
#
# These pages are rendered client-side by Keycloakify, so they need a real
# browser - the server HTML is just a kcContext blob.
#
# Why this lives in the CivicDataSpace suite: the theme repo has no test harness,
# and these pages are where users sign in to this app. The privacy links are the
# seam - the theme builds them as {app}/privacy and test_con_privacy_policy.py
# covers the page they point at.
#
# Design gaps: where production does not yet match the design, the test asserts
# the design and is marked strict xfail with the tracking issue. When a fix
# ships the test XPASSes, strict turns that into a failure, and the marker has
# to come off - at which point it guards the fix.

import os
import uuid

import pytest
import requests

from pages.consumer.keycloak_auth_page import (
    KeycloakErrorPage,
    KeycloakLoginPage,
    KeycloakRegisterPage,
)

pytestmark = [pytest.mark.smoke, pytest.mark.readonly]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

DESIGN_REGISTER_FIELDS = ("email", "password", "password-confirm")


def design_gap(issue, what):
    return pytest.mark.xfail(
        strict=True,
        reason=f"CivicDataLab/DataSpaceKeycloakTheme#{issue}: {what}",
    )


def no_account_email():
    return f"qa-no-account-{uuid.uuid4().hex[:12]}@example.invalid"


@pytest.fixture
def login_page(driver):
    return KeycloakLoginPage(driver).load(BASE_URL)


@pytest.fixture
def register_page(driver):
    return KeycloakRegisterPage(driver).load(BASE_URL)


@pytest.fixture
def reset_page(login_page):
    return login_page.go_to_forgot_password()


class TestSignInPage:
    def test_google_sign_in_is_offered(self, login_page):
        """Google is a configured IdP on the realm and must reach the user."""
        assert login_page.has_google_button(), (
            "No 'Continue with Google' link on the sign-in page. Google is "
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

    def test_google_button_reaches_google(self, login_page):
        """The broker must hand off to Google. Follows the redirect only; never signs in."""
        host = login_page.follow_google()
        assert host == "accounts.google.com", (
            f"Continue with Google landed on {host!r}, not Google's sign-in. "
            "The realm's Google identity provider is misconfigured or its "
            "credentials have been rotated."
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

    def test_heading_and_subtitle_match_design(self, login_page):
        assert login_page.heading() == "Welcome back"
        assert login_page.subtitle() == "Sign in to continue to CivicDataSpace."

    def test_fields_are_labelled_as_designed(self, login_page):
        assert login_page.label_texts() == ("Email *", "Password *")
        assert login_page.placeholders() == ("you@example.org", "Enter your password")

    def test_links_match_design(self, login_page):
        assert login_page.forgot_link_text() == "Forgot password?"
        assert login_page.register_prompt_text() == "Don't have an account? Create an account"
        assert login_page.google_button_text() == "Continue with Google"
        assert login_page.google_button_has_icon(), "Google button has no Google icon"

    def test_back_to_home_returns_to_the_app(self, login_page):
        href = login_page.back_to_home_href() or ""
        assert href.rstrip("/") == BASE_URL.rstrip("/"), (
            f"'Back to Home' points at {href!r}, not the app that started the "
            f"sign-in ({BASE_URL}). The theme derives it from redirect_uri."
        )

    def test_password_visibility_toggle(self, login_page):
        assert login_page.password_state() == ("password", "Show password")
        login_page.toggle_password()
        assert login_page.password_state() == ("text", "Hide password")
        login_page.toggle_password()
        assert login_page.password_state() == ("password", "Show password")

    @design_gap(39, "empty sign-in goes to the server instead of inline required-field errors")
    def test_empty_sign_in_is_validated_inline(self, login_page):
        login_page.submit()
        assert not login_page.document_was_replaced(), (
            "An empty form was sent to the server instead of being checked in the browser."
        )
        errors = login_page.field_errors()
        assert "Email is required." in errors and "Password is required." in errors, errors

    @design_gap(39, "credential error reads 'Invalid username or password.' under Email")
    def test_wrong_credentials_message_matches_design(self, login_page):
        login_page.sign_in(no_account_email(), "NotARealPassword1")
        assert login_page.field_errors() == ["Email or password is incorrect."]


class TestForgotPasswordPage:
    def test_copy_matches_design(self, reset_page):
        assert reset_page.heading() == "Reset your password"
        assert reset_page.subtitle() == (
            "Enter your email address and we'll send you a link to reset your password."
        )
        assert reset_page.submit_label() == "Send Reset Link"
        assert reset_page.back_to_sign_in_text() == "Back to Sign In"

    @design_gap(40, "email typed on Sign In is not carried to the reset form")
    def test_email_carries_over_from_sign_in(self, login_page):
        email = no_account_email()
        reset_page = login_page.type_email(email).go_to_forgot_password()
        assert reset_page.email_value() == email

    @design_gap(40, "empty reset request reads 'Please specify username.'")
    def test_empty_request_message_matches_design(self, reset_page):
        reset_page.request_reset("")
        assert "Email is required." in reset_page.field_errors()

    @design_gap(33, "reset request returns to Sign In with a banner instead of 'Check your email'")
    def test_request_shows_check_your_email(self, reset_page):
        reset_page.request_reset(no_account_email())
        assert reset_page.heading() == "Check your email"


class TestRegistrationPage:
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

    def test_heading_and_links_match_design(self, register_page):
        assert register_page.heading() == "Create your account"
        assert register_page.subtitle() == (
            "Join CivicDataSpace to create, manage and share civic data and knowledge."
        )
        assert register_page.sign_in_prompt_text() == "Already have an account? Sign in"
        assert register_page.has_google_button(), "No 'Continue with Google' on the register page"

    def test_consent_is_enforced_in_the_browser(self, register_page):
        """Unticked consent must stop the form before anything reaches the server."""
        register_page.submit_without_consent()
        assert not register_page.document_was_replaced(), (
            "The form was posted to the server with consent unticked."
        )
        assert register_page.terms_error_text(), "No error shown for missing consent"

    @design_gap(44, "realm renders email, firstName, lastName and no password fields")
    def test_registration_form_renders_design_fields(self, register_page):
        names = register_page.field_names()
        missing = [f for f in DESIGN_REGISTER_FIELDS if f not in names]
        extra = [f for f in ("firstName", "lastName") if f in names]
        assert not missing and not extra, (
            f"Register form fields differ from the design. Missing {missing}, "
            f"not in design {extra}. Present: {names}"
        )

    @design_gap(41, "no live password requirements checklist (and no password field until #44)")
    def test_password_requirements_are_shown(self, register_page):
        assert register_page.type_password("abc"), "No password field on the register form"
        text = register_page.card_text()
        for line in ("Password must contain", "At least 8 characters", "One uppercase letter", "One number"):
            assert line in text, f"{line!r} not shown while typing a password"

    @design_gap(42, "consent covers the Privacy Policy only, not Terms & Conditions")
    def test_consent_covers_terms_and_privacy(self, register_page):
        text = register_page.terms_text()
        assert "Terms & Conditions" in text and "Privacy Policy" in text, text


class TestErrorPage:
    @design_gap(32, "every error page is titled 'Google sign-in failed'")
    def test_bad_redirect_uri_is_not_blamed_on_google(self, driver):
        page = KeycloakErrorPage(driver).load_with_redirect(BASE_URL, "https://example.invalid/cb")
        assert page.heading() != "Google sign-in failed"

    @design_gap(32, "every error page is titled 'Google sign-in failed'")
    def test_unknown_client_is_not_blamed_on_google(self, driver):
        page = KeycloakErrorPage(driver).load_with_client(BASE_URL, "qa-no-such-client")
        assert page.heading() != "Google sign-in failed"


class TestLegalLinks:
    @design_gap(43, "brand panel footer shows only 'Privacy'")
    def test_footer_has_privacy_terms_legal(self, login_page):
        assert login_page.legal_link_texts() == ["Privacy", "Terms", "Legal"]

    @pytest.mark.mobile
    def test_mobile_sign_in_has_no_horizontal_scroll(self, login_page):
        login_page.use_mobile_viewport()
        assert not login_page.has_horizontal_scroll()

    @pytest.mark.mobile
    @design_gap(43, "no legal links at all on mobile")
    def test_mobile_shows_legal_links(self, login_page):
        login_page.use_mobile_viewport()
        assert login_page.visible_legal_link_texts(), "No Privacy/Terms/Legal link visible at 390px"
