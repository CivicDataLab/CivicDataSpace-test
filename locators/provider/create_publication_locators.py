# locators/provider/create_publication_locators.py
#
# The publication wizard (/publications/edit/<id>/{files,details,publish}).
# Shared wizard parts: EditorWizardLocators.

from selenium.webdriver.common.by import By

from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class CreatePublicationLocators:
    CREATE_BUTTON = (By.XPATH, "//main//button[normalize-space()='Create Publication']")

    ADD_YOUTUBE_TOGGLE = (By.XPATH, "//main//button[contains(normalize-space(),'Add a YouTube video instead')]")
    YOUTUBE_URL_INPUT = (By.XPATH, "//input[@name='youtubeUrl']")
    ADD_VIDEO_BUTTON = (By.XPATH, "//main//button[normalize-space()='Add video']")
    FILES_READY = (By.XPATH, "//main//*[normalize-space()='Files (1)']")

    RESOURCE_NAME_INPUT = (By.XPATH, "//input[@name='resourceName']")
    DESCRIPTION_INPUT = (By.XPATH, "//textarea[@name='description']")
    DATE_INPUT = (By.XPATH, "//input[@name='publicationDate']")
    RESOURCE_TYPE_SELECT = (By.XPATH, W.SELECT_BY_LABEL.format(label="Resource Type"))
    NO_CONTRIBUTORS = (By.XPATH, "//main//*[normalize-space()='No contributors added yet.']")
