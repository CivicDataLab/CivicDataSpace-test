# locators/consumer/keycloak_auth_locators.py
#
# Selectors for the Keycloak-hosted login and registration pages
# (DataSpaceKeycloakTheme). These pages are served by auth.civicdatalab.in,
# not by the Next.js app, and Keycloakify renders them client-side from the
# kcContext blob - so none of this exists in the server HTML.

from selenium.webdriver.common.by import By


class KeycloakShellLocators:
    """Chrome shared by every page CustomTemplate renders."""

    HEADING = (By.CSS_SELECTOR, ".civic-auth-header h1")
    SUBTITLE = (By.CSS_SELECTOR, ".civic-auth-header .auth-subtitle")
    CARD = (By.CSS_SELECTOR, ".card-pf")
    BACK_TO_HOME = (By.CSS_SELECTOR, ".civic-form-column > a.back-home")
    LEGAL_LINKS = (By.CSS_SELECTOR, ".civic-legal-links a")
    ALERT = (By.CSS_SELECTOR, ".pf-c-alert")
    FIELD_ERROR = (By.CSS_SELECTOR, ".civic-field-error")
    ANY_LINK = (By.TAG_NAME, "a")


class KeycloakLoginLocators:
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.CSS_SELECTOR, "input[type=submit], button[type=submit]")
    USERNAME_LABEL = (By.CSS_SELECTOR, "label[for=username]")
    PASSWORD_LABEL = (By.CSS_SELECTOR, "label[for=password]")
    PASSWORD_TOGGLE = (By.CSS_SELECTOR, "button[aria-controls=password]")
    FORGOT_LINK = (By.CSS_SELECTOR, "a[href*='login-actions/reset-credentials']")
    REGISTER_PROMPT = (By.ID, "kc-registration")
    GOOGLE_ICON = (By.CSS_SELECTOR, "a[href*='/broker/google/login'] svg")

    # "Continue With Google" - an <a> to the broker endpoint, not a form post.
    GOOGLE_BROKER_LINK = (By.CSS_SELECTOR, "a[href*='/broker/google/login']")
    ANY_BROKER_LINK = (By.CSS_SELECTOR, "a[href*='/broker/']")

    REGISTER_LINK = (By.CSS_SELECTOR, "a[href*='login-actions/registration']")
    PRIVACY_LINK = (By.CSS_SELECTOR, "a[href*='/privacy']")


class KeycloakResetLocators:
    USERNAME = (By.ID, "username")
    SUBMIT = (By.CSS_SELECTOR, "#kc-reset-password-form input[type=submit]")
    BACK_TO_SIGN_IN = (By.CSS_SELECTOR, "#kc-registration a")


class KeycloakErrorLocators:
    TRY_AGAIN = (By.ID, "kc-try-again")


class KeycloakRegisterLocators:
    EMAIL = (By.ID, "email")
    FIRST_NAME = (By.ID, "firstName")
    LAST_NAME = (By.ID, "lastName")
    PASSWORD = (By.ID, "password")
    SIGN_IN_PROMPT = (By.ID, "kc-registration")
    GOOGLE_BROKER_LINK = (By.CSS_SELECTOR, "a[href*='/broker/google/login']")
    TERMS_ROW = (By.CSS_SELECTOR, ".civic-terms")
    TERMS_ERROR = (By.ID, "input-error-termsAccepted")

    # The privacy consent checkbox. Note it carries required=false in the DOM,
    # so nothing about the markup guarantees consent is enforced - the tests
    # assert on the outcome of submitting instead.
    TERMS_CHECKBOX = (By.ID, "termsAccepted")

    SUBMIT = (By.CSS_SELECTOR, "input[type=submit], button[type=submit]")
    PRIVACY_LINK = (By.CSS_SELECTOR, "a[href*='/privacy']")
    BACK_TO_LOGIN = (By.CSS_SELECTOR, "a[href*='login-actions'], a[href*='protocol/openid-connect/auth']")
