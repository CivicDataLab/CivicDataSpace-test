# locators/provider/update_profile_locators.py
from selenium.webdriver.common.by import By

class UpdateProfilePageLocators:

    # ProfileShell (DataSpaceFrontend#506) renders the title as an <h1>:
    # "My Profile" for a user, "My Organization Profile" for an org.
    My_Profile_HEADING = (By.XPATH, '//h1[normalize-space()="My Profile" or normalize-space()="My Organization Profile"]')
    FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName" or @name="name"]')
    LAST_NAME_INPUT = (By.XPATH, '//input[@name="lastName"] | //textarea[@name="description"]')
    BIO_TEXT_INPUT = (By.XPATH, '//textarea[@name="bio"] | //textarea[@name="description"]')
    SAVE_BUTTON = (By.XPATH, '//button[normalize-space()="Save changes"]')
    SAVED_TOAST = (By.XPATH, '//*[text()[contains(., "updated successfully")]]')
    # ProfilePictureField: a picked file previews as a blob: <img> beside the input.
    PICTURE_PREVIEW = (By.XPATH, '//input[@id="profile-picture" or @id="organization-logo"]/../..//img[starts-with(@src, "blob:")]')

    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    GET_FIRST_NAME_INPUT = (By.XPATH, '//input[@name="firstName" or @name="name"]')
    GET_LAST_NAME_INPUT = (By.XPATH, '//input[@name="lastName"] | //textarea[@name="description"]')
    GET_BIO_TEXT_INPUT = (By.XPATH, '//textarea[@name="bio"] | //textarea[@name="description"]')
