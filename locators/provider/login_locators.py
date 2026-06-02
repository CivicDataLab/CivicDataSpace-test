# locators/provider/login_locators.py

from selenium.webdriver.common.by import By

class LoginLocators:
    """XPaths for the Keycloak Login page used by both Consumer & Provider flows."""

    # the link that appears in the user-menu dropdown when logged in
    DASHBOARD_LINK = (By.XPATH, "//a[normalize-space(.)='Dashboard']")
    # The outer form/dialog
    FORM = (By.XPATH, "//div[@id='kc-form-wrapper']")
    LOGIN_BUTTON = (By.XPATH, "//button[normalize-space(.)='LOGIN / SIGN UP']")
    # wait for this to know the login form is fully present:
    SIGNIN_BUTTON = (By.XPATH, "//button[normalize-space()='Sign In'] | //input[@id='kc-login' or @type='submit']")
    EMAIL_INPUT = (By.XPATH, "//input[@id='username' or @name='username']")
    PASSWORD_INPUT = (By.XPATH, "//input[@id='password' or @name='password']")