# tests/consumer/functional/test_con_auth_flows.py
#
# End-to-end auth flows on the redesigned Keycloak pages (DataSpaceKeycloakTheme#46),
# against the realm as configured for the release: password on the register form,
# policy of 8 characters + 1 uppercase + 1 digit, and a user-writable termsAccepted.
#
# Two kinds of test live here:
#
#   - TestRegisterValidation / TestSignInValidation are readonly: they type into the
#     forms and submit only what the theme blocks in the browser, so nothing reaches
#     the server. Safe against production.
#   - The rest create throwaway qa-auto-*@example.invalid accounts in the realm dev and
#     prod share. They depend on `keycloak_admin`, which skips without a service account,
#     and every account is deleted in teardown whether the test passed or not.
#
# Google sign-in, linking and review profile need a real Google account and are not
# automated here.

import os
import uuid

import pytest

from pages.consumer.keycloak_auth_page import (
    REGISTER_PASSWORD,
    KeycloakLoginPage,
    KeycloakRegisterPage,
    KeycloakUpdatePasswordPage,
)
from utils.keycloak_admin import KeycloakAdmin

pytestmark = [pytest.mark.functional, pytest.mark.regression]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

RULES = ("At least 8 characters", "One uppercase letter", "One number")


def assert_handed_to_app(driver, keycloak_admin, email):
    """Keycloak signed the account in and sent the browser back to the app.

    The app's NextAuth callback then rejects the code, because these tests start the flow
    with their own state, so the final URL is the app's sign-in page. The session is the proof.
    """
    host = driver.current_url.split("/")[2]
    assert host == BASE_URL.split("/")[2], f"Still on {driver.current_url!r}, not back at the app"
    assert keycloak_admin.user_session_count(email) >= 1, f"No Keycloak session for {email}"


@pytest.fixture
def keycloak_admin():
    if os.getenv("REGISTRATION_TESTS") == "off":
        pytest.skip("REGISTRATION_TESTS=off: no accounts created in the realm dev and prod share")
    admin = KeycloakAdmin()
    if not admin.available():
        pytest.skip("No Keycloak service-account access: skipped rather than risk undeletable accounts")
    return admin


@pytest.fixture
def throwaway_email(keycloak_admin):
    email = f"qa-auto-{uuid.uuid4().hex[:12]}@example.invalid"
    yield email
    keycloak_admin.delete_user_by_email(email)


@pytest.fixture
def register_page(driver):
    return KeycloakRegisterPage(driver).load(BASE_URL)


@pytest.fixture
def login_page(driver):
    return KeycloakLoginPage(driver).load(BASE_URL)


@pytest.mark.readonly
class TestRegisterValidation:
    @pytest.mark.parametrize(
        "password, met",
        [
            ("abc", ()),
            ("abcdefgh", ("At least 8 characters",)),
            ("Abcdefgh", ("At least 8 characters", "One uppercase letter")),
            ("Abcdefg1", RULES),
        ],
        ids=["short", "length-only", "length-and-upper", "all-rules"],
    )
    def test_checklist_ticks_each_rule_as_it_is_met(self, register_page, password, met):
        register_page.type_password(password)
        rules = dict(register_page.password_rules())
        assert tuple(rules) == RULES, f"Checklist shows {list(rules)}, realm policy is {RULES}"
        ticked = tuple(label for label, state in rules.items() if state == "met")
        assert ticked == met, f"For {password!r} the checklist ticks {ticked}, expected {met}"

    def test_weak_password_is_stopped_in_the_browser(self, register_page):
        register_page.fill(f"qa-no-account-{uuid.uuid4().hex[:8]}@example.invalid", password="abcdefgh")
        register_page.accept_terms()
        assert register_page.submit_stays_in_browser(), "A password that fails the checklist was posted"
        assert register_page.field_error("password") == "Password does not meet all requirements."
        unmet = [label for label, state in register_page.password_rules() if state == "invalid"]
        assert unmet == ["One uppercase letter", "One number"], unmet

    def test_mismatched_confirmation_is_stopped_in_the_browser(self, register_page):
        register_page.fill(f"qa-no-account-{uuid.uuid4().hex[:8]}@example.invalid")
        register_page.type_confirm(REGISTER_PASSWORD + "x")
        register_page.accept_terms()
        assert register_page.submit_stays_in_browser(), "Mismatched passwords were posted"
        assert register_page.field_error("password-confirm") == "Passwords do not match."

    def test_invalid_email_is_stopped_in_the_browser(self, register_page):
        register_page.fill("not-an-email")
        register_page.accept_terms()
        assert register_page.submit_stays_in_browser(), "An invalid email was posted"
        assert register_page.field_error("email"), "No error under an invalid email"

    def test_empty_form_flags_every_field(self, register_page):
        assert register_page.submit_stays_in_browser(), "An empty form was posted"
        for field in ("email", "firstName", "lastName", "password", "password-confirm", "termsAccepted"):
            assert register_page.field_error(field), f"No error under {field} on an empty submit"


@pytest.mark.readonly
class TestSignInValidation:
    def test_invalid_email_is_stopped_in_the_browser(self, login_page):
        login_page.type_email("not-an-email")
        assert login_page.submit_stays_in_browser(), "An invalid email was posted"
        assert login_page.field_error("username") == "Enter a valid email address."


class TestRegistration:
    def test_consent_is_recorded_on_the_account(self, register_page, throwaway_email, keycloak_admin):
        register_page.fill(throwaway_email).accept_terms().submit()
        attributes = keycloak_admin.user_attributes(throwaway_email)
        assert attributes is not None, f"No account created. Landed at {register_page.driver.current_url!r}"
        assert attributes.get("termsAccepted") == ["on"], (
            f"Consent was ticked but the account has termsAccepted={attributes.get('termsAccepted')!r}. "
            "The realm attribute must be editable by users or Keycloak drops it on registration."
        )

    def test_existing_email_offers_sign_in(self, register_page, throwaway_email, keycloak_admin):
        assert keycloak_admin.create_user(throwaway_email, REGISTER_PASSWORD), "Could not seed the account"
        register_page.fill(throwaway_email).accept_terms().submit()
        assert "already exists" in register_page.field_error("email"), register_page.field_error("email")
        href = register_page.email_error_sign_in_href() or ""
        assert "/protocol/openid-connect/auth" in href or "login-actions/authenticate" in href, href


class TestSignIn:
    def test_verified_account_reaches_the_app(self, login_page, throwaway_email, keycloak_admin):
        assert keycloak_admin.create_user(throwaway_email, REGISTER_PASSWORD), "Could not seed the account"
        login_page.sign_in_as(throwaway_email, REGISTER_PASSWORD)
        assert_handed_to_app(login_page.driver, keycloak_admin, throwaway_email)

    def test_unverified_account_is_asked_to_verify(self, login_page, throwaway_email, keycloak_admin):
        assert keycloak_admin.create_user(
            throwaway_email, REGISTER_PASSWORD, email_verified=False, required_actions=["VERIFY_EMAIL"]
        ), "Could not seed the account"
        login_page.sign_in_as(throwaway_email, REGISTER_PASSWORD)
        assert login_page.wait_until_url_contains("VERIFY_EMAIL"), (
            f"An unverified account was not sent to Verify email: {login_page.driver.current_url!r}"
        )


class TestUpdatePassword:
    """The custom update-password page, reached through the UPDATE_PASSWORD required action."""

    @pytest.fixture
    def update_page(self, login_page, throwaway_email, keycloak_admin):
        assert keycloak_admin.create_user(
            throwaway_email, REGISTER_PASSWORD, required_actions=["UPDATE_PASSWORD"]
        ), "Could not seed the account"
        login_page.sign_in_as(throwaway_email, REGISTER_PASSWORD)
        return KeycloakUpdatePasswordPage(login_page.driver).wait_loaded()

    def test_page_matches_design(self, update_page):
        assert update_page.heading() == "Update your password"
        assert update_page.subtitle() == "Choose a new password for your CivicDataSpace account."

    def test_weak_password_is_stopped_in_the_browser(self, update_page):
        update_page.type_new("abcdefgh").type_confirm("abcdefgh")
        assert update_page.submit_stays_in_browser(), "A password that fails the checklist was posted"
        assert update_page.field_error("password-new") == "Password does not meet all requirements."
        unmet = [label for label, state in update_page.password_rules() if state == "invalid"]
        assert unmet == ["One uppercase letter", "One number"], unmet

    def test_mismatch_is_stopped_in_the_browser(self, update_page):
        update_page.type_new("Abcdefg1").type_confirm("Abcdefg2")
        assert update_page.submit_stays_in_browser(), "Mismatched passwords were posted"
        assert update_page.field_error("password-confirm") == "Passwords do not match."

    def test_valid_password_continues_to_the_app(self, update_page, throwaway_email, keycloak_admin):
        update_page.type_new("Newpass-2026A").type_confirm("Newpass-2026A").submit()
        assert keycloak_admin.required_actions(throwaway_email) == [], "UPDATE_PASSWORD is still pending"
        assert_handed_to_app(update_page.driver, keycloak_admin, throwaway_email)
