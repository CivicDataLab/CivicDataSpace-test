# pages/provider/update_profile_page.py

import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from pages.base_page import BasePage
from locators.provider.update_profile_locators import UpdateProfilePageLocators

class UpdateProfilePage(BasePage):

    def is_loaded(self):
        """User ("My Profile") or organization ("My Organization Profile") profile page."""
        return self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(UpdateProfilePageLocators.My_Profile_HEADING)
        )

    def enter_first_name(self, url: str):
        self.clear_and_type(UpdateProfilePageLocators.FIRST_NAME_INPUT, url)
        return self

    def enter_last_name(self, url: str):
        self.clear_and_type(UpdateProfilePageLocators.LAST_NAME_INPUT, url)
        return self

    def enter_bio_text(self, url: str):
        self.clear_and_type(UpdateProfilePageLocators.BIO_TEXT_INPUT, url)
        return self

    def upload_profile_image(self, path_to_file: str):
        """
        Sends the file to ProfilePictureField's file input (the first on the page).
        """
        return self.upload_file_to_dropzone(path_to_file)

    def click_save(self):
        """Click "Save changes" and wait for the "... updated successfully" toast."""
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(UpdateProfilePageLocators.SAVE_BUTTON))
        btn.click()
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(UpdateProfilePageLocators.SAVED_TOAST),
            message="No 'updated successfully' toast after Save changes",
        )
        return self

    def reload(self):
        self.driver.refresh()
        self.is_loaded()
        # The form fills from a query after the heading renders.
        self.wait_with_timeout(20).until(
            lambda d: d.find_element(*UpdateProfilePageLocators.GET_FIRST_NAME_INPUT).get_attribute("value")
        )
        return self

    def get_first_name_value(self):
        return self.driver.find_element(*UpdateProfilePageLocators.GET_FIRST_NAME_INPUT).get_attribute("value")

    def get_last_name_value(self):
        return self.driver.find_element(*UpdateProfilePageLocators.GET_LAST_NAME_INPUT).get_attribute("value")

    def get_bio_text_value(self):
        return self.driver.find_element(*UpdateProfilePageLocators.GET_BIO_TEXT_INPUT).get_attribute("value")

    def is_profile_image_uploaded(self):
        """True once a picked file shows as a blob: preview (before save)."""
        try:
            self.wait.until(EC.visibility_of_element_located(UpdateProfilePageLocators.PICTURE_PREVIEW))
            return True
        except TimeoutException:
            return False
