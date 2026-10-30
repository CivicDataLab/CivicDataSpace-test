# locators/provider/create_usecase_locators.py
#
# Use-case-only fields. Shared wizard parts: EditorWizardLocators.

from selenium.webdriver.common.by import By
from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class CreateUsecaseLocators:
    """/usecases/edit/<id>/{builder,connect,publish}"""

    TITLE_INPUT = (By.XPATH, "//input[@name='useCaseTitle']")
    SUBTITLE_INPUT = (By.XPATH, "//input[@name='useCaseSubtitle']")

    # Builder "Content": Add Content opens a menu of block types.
    ADD_CONTENT_BUTTON = (By.XPATH, "//button[normalize-space()='Add Content']")
    CONTENT_BLOCK_TYPE = "//button[contains(@class,'menuItem') and normalize-space()='{kind}']"
    TEXT_BLOCK_EDITOR = (By.XPATH, "(//div[contains(@class,'ql-editor') and @data-placeholder='Write some text...'])[last()]")

    # Read by tests/test_pill_locators.py to keep chip getters field-scoped.
    SECTOR_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="Sectors"))
    SDG_GOALS_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="SDG Goals"))
    TAG_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="Tags"))
    GEOGRAPHY_CHIPS = (By.XPATH, W.FIELD_CHIPS.format(label="Geography"))
