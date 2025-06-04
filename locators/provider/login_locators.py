# locators/provider/login_locators.py

class LoginLocators:
    """XPaths for the Keycloak Login page used by both Consumer & Provider flows."""



    # the link that appears in the user-menu dropdown when logged in
    DASHBOARD_LINK = "//a[normalize-space(.)='Dashboard']"
    # The outer form/dialog
    FORM = "//div[@id='kc-form-wrapper']"
    LOGIN_BUTTON = "//button[normalize-space(.)='LOGIN / SIGN UP']"
    # wait for this to know the login form is fully present:
    SIGNIN_BUTTON = "//input[@id='kc-login' or @type='submit']"
    EMAIL_INPUT = "//input[@id='username' or @name='username']"
    PASSWORD_INPUT = "//input[@id='password' or @name='password']"