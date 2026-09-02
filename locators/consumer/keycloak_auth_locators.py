# locators/consumer/keycloak_auth_locators.py
#
# Selectors for the Keycloak-hosted login and registration pages
# (DataSpaceKeycloakTheme). These pages are served by auth.civicdatalab.in,
# not by the Next.js app, and Keycloakify renders them client-side from the
# kcContext blob - so none of this exists in the server HTML.

from selenium.webdriver.common.by import By


class KeycloakLoginLocators:
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.CSS_SELECTOR, "input[type=submit], button[type=submit]")

    # "Continue With Google" - an <a> to the broker endpoint, not a form post.
    GOOGLE_BROKER_LINK = (By.CSS_SELECTOR, "a[href*='/broker/google/login']")
    ANY_BROKER_LINK = (By.CSS_SELECTOR, "a[href*='/broker/']")

    REGISTER_LINK = (By.CSS_SELECTOR, "a[href*='login-actions/registration']")
    PRIVACY_LINK = (By.CSS_SELECTOR, "a[href*='/privacy']")


class KeycloakRegisterLocators:
    EMAIL = (By.ID, "email")
    FIRST_NAME = (By.ID, "firstName")
    LAST_NAME = (By.ID, "lastName")

    # The privacy consent checkbox. Note it carries required=false in the DOM,
    # so nothing about the markup guarantees consent is enforced - the tests
    # assert on the outcome of submitting instead.
    TERMS_CHECKBOX = (By.ID, "termsAccepted")

    SUBMIT = (By.CSS_SELECTOR, "input[type=submit], button[type=submit]")
    PRIVACY_LINK = (By.CSS_SELECTOR, "a[href*='/privacy']")
    BACK_TO_LOGIN = (By.CSS_SELECTOR, "a[href*='login-actions'], a[href*='protocol/openid-connect/auth']")
