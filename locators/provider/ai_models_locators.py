# locators/provider/ai_models_locators.py
#
# AI-model-only parts. Shared wizard parts: EditorWizardLocators.

from selenium.webdriver.common.by import By


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
    SAVE_VERSION_BTN = (By.XPATH, "//button[normalize-space()='Save Version']")
    SAVED_VERSION = "//main//*[normalize-space()='Version {name}']"

    # Model Information
    MODEL_NAME_INPUT = (By.XPATH, "//input[@name='modelName']")
    DESCRIPTION_EDITOR = (By.XPATH, "//main//div[contains(@class,'ql-editor') and @contenteditable='true']")
    INTENDED_USE_INPUT = (By.XPATH, "//textarea[@name='intendedUse']")
    MODEL_WEBSITE_INPUT = (By.XPATH, "//input[@name='modelWebsite']")
    USAGE_LICENSE_SELECT = (By.XPATH, "//button[@id=//label[normalize-space()='Usage License']/@for]")

    # A button-style select's options live in the element its trigger controls.
    SELECT_OPTION = "//*[@id='{listbox}']//*[@role='option' and normalize-space()='{text}']"
    LISTBOX_OPTIONS = "//*[@id='{listbox}']//*[@role='option']"
