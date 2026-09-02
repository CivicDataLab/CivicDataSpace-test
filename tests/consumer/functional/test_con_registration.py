# tests/consumer/functional/test_con_registration.py
#
# The registration flow on the Keycloak-hosted form, including whether the
# privacy consent checkbox is actually enforced.
#
# These tests CREATE REAL USERS in the realm. Two rules follow from that:
#
#   1. Never create an account we cannot delete. Every test here depends on
#      the `keycloak_admin` fixture, which skips the test outright if a
#      service-account token cannot be obtained. A missing secret produces a
#      skip, never a stray account.
#   2. Cleanup runs in fixture teardown, so it happens even when the test
#      fails mid-flow. Deletion is by exact email and is a no-op when nothing
#      was created, which is the expected path in the consent test.
#
# Emails use the .invalid TLD (RFC 2606) so a stray account can never
# correspond to a deliverable address.
#
# Behaviour these assertions are built on, verified against dev:
#   - submitting without consent  -> form does not go through, no user created
#   - submitting with consent     -> user created, redirect to VERIFY_EMAIL
#
# The consent test matters more than it looks: termsAccepted carries
# required=false in the DOM, so nothing in the markup enforces it. Only the
# outcome tells you whether consent is real.

import os
import uuid

import pytest

from pages.consumer.keycloak_auth_page import KeycloakRegisterPage
from utils.keycloak_admin import KeycloakAdmin

pytestmark = [pytest.mark.functional, pytest.mark.regression]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")


@pytest.fixture
def keycloak_admin():
    """Admin client, or skip. Guarantees anything created can be removed."""
    admin = KeycloakAdmin()
    if not admin.available():
        pytest.skip(
            "No Keycloak service-account access (KEYCLOAK_URL / REALM / "
            "CLIENT_ID / CLIENT_SECRET). Registration tests are skipped "
            "rather than risk creating accounts that cannot be cleaned up."
        )
    return admin


@pytest.fixture
def throwaway_email(keycloak_admin):
    """A unique address, purged in teardown whether or not the test passed."""
    email = f"qa-auto-{uuid.uuid4().hex[:12]}@example.invalid"
    yield email
    keycloak_admin.delete_user_by_email(email)


@pytest.fixture
def register_page(driver):
    return KeycloakRegisterPage(driver).load(BASE_URL)


class TestPrivacyConsentEnforcement:
    """The consent checkbox must actually gate registration."""

    def test_registration_is_blocked_without_consent(
        self, register_page, throwaway_email, keycloak_admin
    ):
        """Submitting without ticking consent must not create an account.

        Asserted on the outcome rather than the markup: the checkbox is
        required=false, so only the realm's behaviour is evidence.
        """
        register_page.fill(throwaway_email)
        assert not register_page.terms_is_checked(), (
            "Consent box was pre-ticked; this test cannot verify enforcement."
        )
        register_page.submit()

        assert not keycloak_admin.user_exists(throwaway_email), (
            f"An account was created for {throwaway_email} WITHOUT the privacy "
            "consent box being ticked. Users are being registered without "
            "recorded consent."
        )
        assert register_page.still_on_registration_form(), (
            "Registration left the form without consent. It did not create an "
            "account, but the user was moved on regardless - the flow should "
            f"keep them on the form. URL: {register_page.driver.current_url!r}"
        )


class TestRegistrationFlow:
    """Full registration, through to an account existing in the realm."""

    def test_registration_with_consent_creates_an_account(
        self, register_page, throwaway_email, keycloak_admin
    ):
        register_page.fill(throwaway_email).accept_terms()
        assert register_page.terms_is_checked(), "Consent box did not tick"
        register_page.submit()

        assert keycloak_admin.user_exists(throwaway_email), (
            f"Registration completed but no account exists for {throwaway_email}. "
            f"Landed at {register_page.driver.current_url!r}. Body: "
            f"{register_page.body_text()[:300]!r}"
        )

    def test_registration_requires_email_verification(
        self, register_page, throwaway_email, keycloak_admin
    ):
        """A new account must land on VERIFY_EMAIL, not straight into the app.

        Guards the account being usable before the address is proven.
        """
        register_page.fill(throwaway_email).accept_terms().submit()

        assert register_page.reached_verify_email(), (
            "Registration did not route to the VERIFY_EMAIL required action. "
            "A new account may be usable without its email being verified. "
            f"URL: {register_page.driver.current_url!r}"
        )
        assert throwaway_email in register_page.body_text(), (
            "The verification screen does not name the address it sent to, so "
            "a user cannot tell which mailbox to check."
        )
