# locators/provider/create_dataset_locators.py
#
# Dataset-only parts of the wizard (/dataset/<id>/edit/{resources,metadata,publish}).
# Shared wizard parts: EditorWizardLocators.

from locators.provider.editor_wizard_locators import EditorWizardLocators as W


class CreateDatasetLocators:
    # ---- Dataset type modal (from "Create Dataset" on the list) ----
    MODAL_TITLE = "//h2[contains(., 'Create New Dataset')] | //div[contains(., 'Select the type of dataset')]"
    DATA_DATASET_CARD = "//button[.//h3[normalize-space()='Data Dataset']]"
    PROMPT_DATASET_CARD = "//button[.//h3[normalize-space()='Prompt Dataset']]"
    # Scoped to the modal: the header has its own "Create Dataset" button.
    CREATE_DATASET_BUTTON = "//div[@role='dialog']//button[normalize-space()='Create Dataset']"

    # ---- Steps: buttons in the Progress nav, labelled then subtitled ----
    STEP_BUTTON = "//main//button[starts-with(normalize-space(),'{label}')]"
    # Creating a dataset lands on Data Files, where this step button is the first sign of the editor.
    TAB_METADATA = STEP_BUTTON.format(label="Metadata")

    # ---- Metadata ----
    TITLE_INPUT = "//input[@name='title']"
    DESCRIPTION = "//main//div[contains(@class, 'ql-editor') and @contenteditable='true']"
    DATE_CREATED_INPUT = W.FIELD_INPUT.format(label="Date of Creation of Dataset")
    SOURCE_INPUT = "//input[@id=//label[normalize-space()='Source Website']/@for]"
    LICENSE_SELECT = W.SELECT_BY_LABEL.format(label="License")

    # Read by tests/test_pill_locators.py to keep chip getters field-scoped.
    SECTOR_CHIPS = W.FIELD_CHIPS.format(label="Sector")
    TAG_CHIPS = W.FIELD_CHIPS.format(label="Tags")
    GEOGRAPHY_CHIPS = W.FIELD_CHIPS.format(label="Geography")

    # ---- Data Files / Prompt Files ----
    DATAFILES_INPUT = "//main//input[@type='file']"
    # One <article> per uploaded file, labelled by its name.
    UPLOADED_FILE_NAMES = "//main//article//p[@id=ancestor::article[1]/@aria-labelledby]"
    UPLOADED_FILE_NAME = UPLOADED_FILE_NAMES + "[normalize-space()='{name}']"
    VIEW_FILE_BUTTON = "//main//article[.//p[normalize-space()='{name}']]//button[normalize-space()='View']"
    PROMPT_FILE_SHEET = "//*[@role='dialog'][.//h2[normalize-space()='Prompt File Details']]"
    SHEET_CLOSE_BUTTON = PROMPT_FILE_SHEET + "//button[normalize-space()='Close']"

    # ---- Review & Publish ----
    PUBLISH_DATASET_BUTTON = "//main//button[normalize-space()='Publish Dataset']"
