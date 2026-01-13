# locators/HomepageLocators.py

from selenium.webdriver.common.by import By

class HomepageLocators:
    ICON                = (By.XPATH, "/html/body/main/div/header/nav/div/div[1]/a/div/div/div[1]/img")
    TAB_DATASETS        = (By.XPATH, "/html/body/main/div/header/nav/div/div[2]/div[2]/div[1]/a")
    TAB_SECTORS         = (By.XPATH, "/html/body/main/div/header/nav/div/div[2]/div[2]/div[2]/a")
    TAB_USECASES        = (By.XPATH, "/html/body/main/div/header/nav/div/div[2]/div[2]/div[3]/a")
    TAB_PUBLISHERS      = (By.XPATH, "/html/body/main/div/header/nav/div/div[2]/div[2]/div[4]/a")
    TAB_ABOUT           = (By.XPATH, "/html/body/main/div/header/nav/div/div[2]/div[2]/div[5]/a")
    LOGIN_SIGNUP_BUTTON = (By.XPATH, "/html/body/main/div/header/nav/div/div[2]/div[3]/button")
    LOGOUT_PROFILE_LOGO = (By.XPATH, "//button[.//div[contains(@class, 'Avatar-module_Wrapper')]]")
    LOGOUT              = (By.XPATH, "//button[normalize-space()='Log Out']")