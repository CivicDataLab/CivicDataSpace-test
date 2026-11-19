# locators/provider/ai_models_locators.py
#
# AI-model-only parts. Shared wizard parts: EditorWizardLocators.

from selenium.webdriver.common.by import By
from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class AiModelsLocators:

    # ── List page ─────────────────────────────────────────────────────────────
    ADD_NEW_AI_MODEL_BTN = (By.XPATH, "//button[normalize-space()='Create AI Model']")

    # ── Wizard: /aimodels/edit/<id>/{versions,details,publish} ────────────────
    # Versions: "Add Version" opens a sheet holding the version and its access methods.
    ADD_VERSION_BTN = (By.XPATH, "//button[normalize-space()='Add Version']")
    VERSION_SHEET = (By.XPATH, "//*[@role='dialog'][.//h2[normalize-space()='Add Version']]")
    ADD_ACCESS_METHOD_BTN = (By.XPATH, "(//*[@role='dialog']//button[normalize-space()='Add Access Method'])[last()]")
    ACCESS_NAME_INPUT = (By.XPATH, "//input[@name='accessName']")
    PROVIDER_SELECT = (By.XPATH, "//*[@role='dialog']//button[@role='combobox'][normalize-space()='Select provider...']")
    PROVIDER_MODEL_ID_INPUT = (By.XPATH, "//input[@name='providerModelId']")
    API_ENDPOINT_INPUT = (By.XPATH, "//input[@name='apiEndpointUrl']")
    VERSION_NAME_INPUT = (By.XPATH, "//input[@name='sheetVersionName']")
    LIFECYCLE_SELECT = (By.XPATH, "//input[@name='sheetVersionName']/following::button[@role='combobox'][1]")
    PROVIDER_TYPE_SELECT = (By.XPATH, "//input[@name='accessName']/following::button[@role='combobox'][1]")
    AUTH_TYPE_SELECT = (By.XPATH, "//input[@name='apiEndpointUrl']/following::button[@role='combobox'][1]")
    VISIBLE_OPTIONS = (By.XPATH, "//*[@role='listbox']//*[@role='option']")
    SHEET_FIELDS = (By.XPATH, "//*[@role='dialog']//*[self::input or self::textarea][@name]")
    SHEET_LABELS = (By.XPATH, "//*[@role='dialog']//label")
    SHEET_CANCEL_BTN = (By.XPATH, "(//*[@role='dialog']//button[normalize-space()='Cancel'])[last()]")
    VERSION_ROWS = (By.XPATH, "//main//*[starts-with(normalize-space(.),'Version ') and not(.//*[starts-with(normalize-space(.),'Version ')])]")
    EDIT_VERSION_TITLE = (By.XPATH, "//*[@role='dialog']//h2[normalize-space()='Edit Version']")
    SAVE_VERSION_BTN = (By.XPATH, "//button[normalize-space()='Save Version']")
    SAVED_VERSION = "//main//*[normalize-space()='Version {name}']"

    # Model Information
    MODEL_NAME_INPUT = (By.XPATH, "//input[@name='modelName']")
    DESCRIPTION_EDITOR = (By.XPATH, "//main//div[contains(@class,'ql-editor') and @contenteditable='true']")
    INTENDED_USE_INPUT = (By.XPATH, "//textarea[@name='intendedUse']")
    MODEL_WEBSITE_INPUT = (By.XPATH, "//input[@name='modelWebsite']")
    USAGE_LICENSE_SELECT = (By.XPATH, W.SELECT_BY_LABEL.format(label="Usage License"))
