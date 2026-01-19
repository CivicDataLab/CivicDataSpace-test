# locators/HomepageLocators.py

from selenium.webdriver.common.by import By

class HomepageLocators:
    # More resilient relative XPaths (Phase 13)
    ICON                = (By.XPATH, "//header//nav//img[contains(@src, 'logo') or contains(@class, 'logo')]")
    TAB_DATASETS        = (By.XPATH, "//header//nav//a[contains(@href, 'datasets') or contains(., 'Datasets')]")
    TAB_SECTORS         = (By.XPATH, "//header//nav//a[contains(@href, 'sectors') or contains(., 'Sectors')]")
    TAB_USECASES        = (By.XPATH, "//header//nav//a[contains(@href, 'usecases') or contains(., 'Use Cases')]")
    TAB_PUBLISHERS      = (By.XPATH, "//header//nav//a[contains(@href, 'publishers') or contains(., 'Publishers')]")
    TAB_ABOUT           = (By.XPATH, "//header//nav//a[contains(@href, 'about') or contains(., 'About')]")
    LOGIN_SIGNUP_BUTTON = (By.XPATH, "//header//nav//button[contains(., 'LOGIN') or contains(., 'SIGN UP')]")
    LOGOUT_PROFILE_LOGO = (By.XPATH, "//button[.//div[contains(@class, 'Avatar-module_Wrapper')]]")
    LOGOUT              = (By.XPATH, "//button[normalize-space()='Log Out']")

    # Tour popup - using data-test-id for more reliable targeting
    SKIP_TOUR_BUTTON    = (By.XPATH, "//button[@data-test-id='button-skip' or @data-action='skip' or contains(., 'Skip tour')]")