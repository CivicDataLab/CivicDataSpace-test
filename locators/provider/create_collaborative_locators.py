# locators/provider/create_collaborative_locators.py
#
# Collaborative-only fields. Shared wizard parts: EditorWizardLocators.

from selenium.webdriver.common.by import By
from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class CreateCollaborativeLocators:
    """/collaboratives/edit/<id>/{about,people,content,publish}"""

    COLLABORATIVE_NAME_INPUT = (By.XPATH, "//input[@name='title']")
    DESCRIPTION_INPUT = (By.XPATH, "//div[contains(@class, 'ql-editor') and @contenteditable='true']")
    PLATFORM_URL_INPUT = (By.XPATH, "//input[@name='platformUrl']")

    # Read by tests/test_pill_locators.py to keep chip getters field-scoped.
    SECTOR_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="Sectors"))
    SDG_GOALS_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="SDG Goals"))
    TAG_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="Tags"))
    GEOGRAPHY_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="Geography"))
