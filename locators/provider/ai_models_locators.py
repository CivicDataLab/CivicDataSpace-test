# locators/provider/ai_models_locators.py

from selenium.webdriver.common.by import By


class AiModelsLocators:

    # ── List page ─────────────────────────────────────────────────────────────
    ADD_NEW_AI_MODEL_BTN = (By.XPATH, "//button[normalize-space()='Add New AI Model']")

    # ── Editor tabs ───────────────────────────────────────────────────────────
    TAB_METADATA = "//button[@role='tab' and normalize-space()='Metadata']"
    TAB_VERSION  = "//button[@role='tab' and normalize-space()='Version']"
    TAB_PUBLISH  = "//button[@role='tab' and normalize-space()='Publish']"

    # ── Metadata – native <select> fields (by stable `name` attribute) ────────
    # Labels use <label> elements; asterisk is CSS ::after, not in DOM text
    MODEL_TYPE_SELECT    = "//select[@name='modelType']"
    DOMAIN_SELECT        = "//select[@name='domain']"
    MAX_TOKENS_SELECT    = "//select[@name='maxTokens']"
    USAGE_LICENSE_SELECT = "//select[@name='usageLicense']"

    # ── Metadata – Quill rich-text editor ─────────────────────────────────────
    DESCRIPTION_EDITOR = "//div[contains(@class,'ql-editor')]"

    # ── Metadata – text inputs / textareas (by stable `name` attribute) ───────
    TARGET_USERS_INPUT  = "//textarea[@name='targetUsers']"
    INTENDED_USE_INPUT  = "//textarea[@name='intendedUse']"
    MODEL_WEBSITE_INPUT = "//input[@name='modelWebsite']"

    # ── Metadata – custom combobox inputs (via <label> text, no asterisk) ─────
    SECTORS_INPUT   = "//label[normalize-space()='Sectors']/following::input[@role='combobox'][1]"
    TAGS_INPUT      = "//label[normalize-space()='Tags']/following::input[@role='combobox'][1]"
    LANGUAGES_INPUT = "//label[normalize-space()='Languages']/following::input[@role='combobox'][1]"
    GEOGRAPHY_INPUT = "//label[normalize-space()='Locations / Geography']/following::input[@role='combobox'][1]"

    # ── Version tab – main card ───────────────────────────────────────────────
    CREATE_FIRST_VERSION_BTN = "//button[normalize-space()='Create First Version']"
    NEW_VERSION_BTN          = "//button[normalize-space()='NEW VERSION']"
    ADD_ACCESS_METHOD_BTN    = "//button[contains(normalize-space(),'Add Access Method')]"
    NO_VERSIONS_PLACEHOLDER  = "//div[normalize-space()='No versions yet']"

    # ── Version tab – "Add a New Version" dialog ──────────────────────────────
    VERSION_NAME_INPUT     = "//label[normalize-space()='Version Name']/following::input[1]"
    LIFECYCLE_STAGE_SELECT = "//label[normalize-space()='Lifecycle Stage']/following::select[1]"
    SAVE_VERSION_BTN       = "//button[normalize-space()='SAVE AND CLOSE']"

    # ── Version tab – "Add New Access Method" dialog ──────────────────────────
    PROVIDER_TYPE_SELECT = "//label[normalize-space()='Provider Type']/following::select[1]"
    API_ENDPOINT_INPUT   = "//input[@placeholder='https://your-api.com/v1/completions']"
    ADD_PROVIDER_BTN     = "//button[normalize-space()='Add Provider']"

    # ── Metadata – access type ────────────────────────────────────────────────
    # Radix UI Checkbox renders as <button role="checkbox">; the Restricted
    # option has @disabled, so selecting the non-disabled one gives Open Access.
    OPEN_ACCESS_CHECKBOX = "//button[@role='checkbox' and not(@disabled)]"

    # ── Wizard navigation ─────────────────────────────────────────────────────
    WIZARD_NEXT_BTN = "//button[normalize-space()='Next']"

    # ── Publish tab ───────────────────────────────────────────────────────────
    PUBLISH_REVIEW_SECTION  = "//div[contains(normalize-space(),'REVIEW AI MODEL DETAILS')]"
    PUBLISH_BTN             = "//button[normalize-space()='Publish' and not(@role='tab')]"
    MODEL_NOT_PUBLISHED_TXT = "//div[contains(normalize-space(),'Model is not published')]"
    MODEL_PUBLISHED_TXT     = "//div[contains(normalize-space(),'Model is published')]"
    METADATA_MISSING_ERROR  = "//*[contains(normalize-space(),'missing. Please add to continue')]"
