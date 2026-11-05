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
        """
        Check if profile page (individual or organization) is loaded.
        Individual profiles have "My Profile" heading, organizations just have the Save button.
        """
        # Try individual profile heading first
        try:
            return self.wait_with_timeout(10).until(
                EC.visibility_of_element_located(UpdateProfilePageLocators.My_Profile_HEADING)
            )
        except TimeoutException:
            # If not found, try organization profile (Save button)
            return self.wait_with_timeout(10).until(
                EC.visibility_of_element_located((By.XPATH, "//button[starts-with(normalize-space(.),'Save')]"))
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
        Triggers logo upload by clicking visible DropZone and sending keys to hidden input.
        Uses BasePage utility method to eliminate code duplication.
        """
        self._srcs_before = self._image_srcs()
        return self.upload_file_to_dropzone(path_to_file)

    def _image_srcs(self):
        return self.driver.execute_script(
            "return [...document.querySelectorAll('main img')].map(i => i.src)"
        )

    def click_save(self):
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(UpdateProfilePageLocators.SAVE_BUTTON))
        btn.click()
        return self

    def get_first_name_value(self):
        return self.driver.find_element(*UpdateProfilePageLocators.GET_FIRST_NAME_INPUT).get_attribute("value")

    def get_last_name_value(self):
        return self.driver.find_element(*UpdateProfilePageLocators.GET_LAST_NAME_INPUT).get_attribute("value")

    def get_bio_text_value(self):
        return self.driver.find_element(*UpdateProfilePageLocators.GET_BIO_TEXT_INPUT).get_attribute("value")

    def is_profile_image_uploaded(self):
        """True once an avatar image on the page points at a different file than before the upload."""
        try:
            self.wait.until(lambda d: self._image_srcs() != self._srcs_before)
            return True
        except TimeoutException:
            return False
