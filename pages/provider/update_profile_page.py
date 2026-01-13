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
        return self.wait_with_timeout(10).until(
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
        Triggers logo upload by clicking visible DropZone and sending keys to hidden input.
        Uses BasePage utility method to eliminate code duplication.
        """
        return self.upload_file_to_dropzone(path_to_file)

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
        try:
            elt = self.wait.until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, "FileUpload-module_Action__Hg0nE")
                )
            )
            return bool(elt.text.strip())
        except TimeoutException:
            return False