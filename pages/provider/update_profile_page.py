# pages/provider/update_profile_page.py

import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from locators.provider.update_profile_locators import UpdateProfilePageLocators


class UpdateProfilePage(BasePage):

    def is_loaded(self):
        return WebDriverWait(self.driver, 10).until(
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
        """

        # Ensure file is present
        assert os.path.isfile(path_to_file), f"File does not exist: {path_to_file}"

        # First, click anywhere on the DropZone to focus the input (important for React UIs)
        dropzone = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "DropZone-module_DropZone__xD9-6")),
            message="Could not find clickable DropZone"
        )
        dropzone.click()

        # Then get the real <input type="file"> and send keys
        input_el = self.driver.find_element(By.XPATH, "//input[@type='file']")

        self.driver.execute_script("arguments[0].style.display = 'block';", input_el)
        time.sleep(1)  # Give time for UI to stabilize
        input_el.send_keys(path_to_file)

        return self

    def click_save(self):
        btn = WebDriverWait(self.driver, 10).until(
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
        except:
            return False