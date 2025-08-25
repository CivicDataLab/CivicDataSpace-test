# locators/provider/update_profile_locators.py
from selenium.webdriver.common.by import By

class UpdateProfilePageLocators:

    My_Profile_HEADING = (By.XPATH, '//span[normalize-space()="My Profile"]')
    FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName"]')



    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    GET_FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName"]')