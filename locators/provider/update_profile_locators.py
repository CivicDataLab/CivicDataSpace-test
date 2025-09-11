# locators/provider/update_profile_locators.py
from selenium.webdriver.common.by import By

class UpdateProfilePageLocators:

    My_Profile_HEADING = (By.XPATH, '//span[normalize-space()="My Profile"]')
    FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName"]')
    LAST_NAME_INPUT = (By.XPATH, '//input[@name="lastName"]')
    BIO_TEXT_INPUT = (By.XPATH, '//textarea[@name="bio"]')
    SAVE_BUTTON = (By.XPATH, '//span[contains(text(),"Save")]')

    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    GET_FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName"]')
    GET_LAST_NAME_INPUT = (By.XPATH, '//input[@name="lastName"]')
    GET_BIO_TEXT_INPUT = (By.XPATH, '//textarea[@name="bio"]')
    GET_UPDATE_STATUS = (By.XPATH, '/html/body/main/section/ol/li/div/div')