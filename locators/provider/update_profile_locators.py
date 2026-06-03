# locators/provider/update_profile_locators.py
from selenium.webdriver.common.by import By

class UpdateProfilePageLocators:

    My_Profile_HEADING = (By.XPATH, '//span[normalize-space()="My Profile"]')
    FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName" or @name="name"]')
    LAST_NAME_INPUT = (By.XPATH, '//input[@name="lastName"] | //textarea[@name="description"]')
    BIO_TEXT_INPUT = (By.XPATH, '//textarea[@name="bio"] | //textarea[@name="description"]')
    SAVE_BUTTON = (By.XPATH, '//span[contains(text(),"Save")]')

    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    GET_FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName" or @name="name"]')
    GET_LAST_NAME_INPUT = (By.XPATH, '//input[@name="lastName"] | //textarea[@name="description"]')
    GET_BIO_TEXT_INPUT = (By.XPATH, '//textarea[@name="bio"] | //textarea[@name="description"]')
    GET_UPDATE_STATUS = (By.XPATH, '//main//section[@role="alert" or contains(@class, "alert")]//div | //main//li//div[contains(@class, "status")]')
