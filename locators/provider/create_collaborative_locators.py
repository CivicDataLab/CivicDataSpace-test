# locators/provider/create_collaborative_locators.py

from selenium.webdriver.common.by import By

class CreateCollaborativeLocators:
    """
    All locators for the CreateCollaborativePage.
    Keep things as simple constants so that the POM methods can refer to them by name.
    """

    # ─── "Collaborative Details" Tab and Fields ─────────────────────────────────────
    DETAILS_TAB = (By.XPATH, "//button[normalize-space()='Collaborative Details']")

    # Collaborative Name - Edit button and save functionality
    COLLABORATIVE_NAME_EDIT_BUTTON = (By.XPATH, "//div[@class=' pl-2']//button[@type='button']")
    # Try multiple strategies to find the name input
    COLLABORATIVE_NAME_INPUT = (By.XPATH, "//label[contains(text(),'COLLABORATIVE NAME')]/following::input[1]")
    COLLABORATIVE_NAME_INPUT_ALT = (By.CSS_SELECTOR, "input[type='text']")
    COLLABORATIVE_NAME_INPUT_ALT2 = (By.ID, "collaborativeName")
    COLLABORATIVE_NAME_SAVE_BUTTON = (By.XPATH, "//button[normalize-space()='Save']")
    # Locator for the displayed collaborative name (after save)
    COLLABORATIVE_NAME_DISPLAY = (By.XPATH, "//span[contains(text(),'COLLABORATIVE NAME')]/following-sibling::*[1]")
    COLLABORATIVE_NAME_DISPLAY_ALT = (By.XPATH, "//div[contains(@class,'flex')]//div[@class=' pl-2']")
    COLLABORATIVE_NAME_DISPLAY_ALT2 = (By.XPATH, "//label[contains(text(),'COLLABORATIVE NAME')]/following::div[1]")

    # Summary field (rich text editor)
    COLLABORATIVE_SUMMARY_LABEL = (By.XPATH, "//label[normalize-space()='Summary *']")
    COLLABORATIVE_SUMMARY_INPUT = (By.XPATH, "//div[contains(@class, 'ql-editor') and @contenteditable='true']")

    # Platform URL
    PLATFORM_URL_INPUT = (By.XPATH, "//input[@name='platformUrl']")

    # SDG Goals (try both singular and plural)
    SDG_GOALS_CONTAINER = (By.XPATH, "//label[normalize-space()='SDG Goals *']/following::input[1]")
    SDG_GOALS_CONTAINER_ALT = (By.XPATH, "//label[normalize-space()='SDG Goal *']/following::input[1]")
    SDG_GOALS_CONTAINER_ALT2 = (By.XPATH, "//label[contains(text(),'SDG')]/following::input[1]")
    SDG_GOALS_OPTION = "//div[@role='option' and normalize-space(.)='{value}']"

    # Tags
    TAGS_INPUT = (By.XPATH, "//label[normalize-space()='Tags']/following::input[@role='combobox'][1]")
    TAG_DROPDOWN_ITEM = "//div[@role='option' and normalize-space(.)='{value}']"

    # Sectors
    SECTOR_INPUT = (By.XPATH, "//label[normalize-space()='Sectors *']/following::input[@role='combobox'][1]")
    SECTOR_DROPDOWN_ITEM = "//div[@role='option' and normalize-space(.)='{value}']"

    # Geography
    GEOGRAPHY_CONTAINER = (By.XPATH, "//label[normalize-space()='Geographies']/following::input[1]")
    GEO_OPTION = "//div[@role='option' and starts-with(normalize-space(.), '{value}')]"

    # Dates
    STARTED_ON_INPUT = (By.XPATH, "//input[@type='date' and @name='startedOn']")
    COMPLETED_ON_INPUT = (By.XPATH, "//input[@type='date' and @name='completedOn']")

    # Logo Upload
    LOGO_UPLOAD_INPUT = (By.XPATH, "//label[normalize-space()='Logo *']/following::div[contains(@class,'FileUpload-module_Action')][1]")

    # Cover Image Upload
    COVER_IMAGE_UPLOAD_INPUT = (By.XPATH, "//label[normalize-space()='Cover Image']/following::div[contains(@class,'FileUpload-module_Action')][1]")

    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    SUMMARY_INPUT = (By.XPATH, "//div[contains(@class, 'ql-editor') and @contenteditable='true']")
    STARTED_ON_VALUE_INPUT = (By.XPATH, "//input[@type='date' and @name='startedOn']")
    COMPLETED_ON_VALUE_INPUT = (By.XPATH, "//input[@type='date' and @name='completedOn']")

    # ─── Tags / Sectors / SDG Goals / Geography Chips (Assertions) ─────────────────────────
    SELECTED_TAGS = "//label[normalize-space()='Tags']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_SECTORS = "//label[normalize-space()='Sectors' or normalize-space()='Sectors *']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_GEOGRAPHY = "//label[normalize-space(text())='Geographies']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_SDG_GOALS = "//label[normalize-space()='SDG Goals *' or normalize-space()='SDG Goal *' or contains(normalize-space(),'SDG')]/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"

    # ─── Logo & Cover Image Preview (Post-upload Check) ──────────────────────────────────────
    LOGO_PREVIEW = (By.CSS_SELECTOR, ".uploaded-logo-preview")
    COVER_IMAGE_PREVIEW = (By.CSS_SELECTOR, ".uploaded-cover-preview")

    # ─── Navigation Buttons ─────────────────────────────────────────────────────────────
    NEXT_BUTTON = (By.XPATH, "//button[normalize-space()='Next']")
    PREVIOUS_BUTTON = (By.XPATH, "//button[normalize-space()='Previous']")

    # ─── "Datasets" Tab (if applicable) ────────────────────────────────────────────────────────
    DATASETS_TAB = (By.XPATH, "//button[normalize-space()='Datasets']")
    FIRST_DATASET_CHECKBOX = (By.XPATH, "//tbody/tr[1]//button[@role='checkbox']")
    SELECTED_DATASET_CHECKBOX = (By.XPATH, "//tbody/tr[1]//button[@data-state='checked' and @aria-checked='true']")
    SUBMIT_DATASETS_BUTTON = (By.XPATH, "//button[normalize-space()='Submit']")

    # ─── "Use Cases" Tab (if applicable) ────────────────────────────────────────────────────────
    USECASES_TAB = (By.XPATH, "//button[normalize-space()='Use Cases']")
    FIRST_USECASE_CHECKBOX = (By.XPATH, "//tbody/tr[1]//button[@role='checkbox']")
    SELECTED_USECASE_CHECKBOX = (By.XPATH, "//tbody/tr[1]//button[@data-state='checked' and @aria-checked='true']")
    SUBMIT_USECASES_BUTTON = (By.XPATH, "//button[normalize-space()='Submit']")

    # ─── "Contributors" Tab ────────────────────────────────────────────────────
    CONTRIBUTORS_TAB = (By.XPATH, "//button[normalize-space()='Contributors']")
    CONTRIBUTORS_INPUT = (By.XPATH, "//input[@placeholder='Add Contributors']")
    SUPPORTERS_INPUT = (By.XPATH, "//input[@placeholder='Add Supporters']")
    PARTNERS_INPUT = (By.XPATH, "//input[@placeholder='Add Partners']")

    # ─── Contributors/Sponsors List Items ──────────────────────────────────────
    CONTRIBUTORS_LIST_ITEMS = (
        By.XPATH,
        "//div[contains(@class,'flex') and contains(@class,'gap-2')]/span[contains(@class, 'Text-module_bodyMd')]"
    )
    SUPPORTERS_LIST_ITEMS = (By.CSS_SELECTOR, ".supporters-list-item")
    PARTNERS_LIST_ITEMS = (By.CSS_SELECTOR, ".partners-list-item")

    # ─── "Publish" Tab ─────────────────────────────────────────────────────────
    PUBLISH_TAB = (By.XPATH, "//button[normalize-space()='Publish']")
    PUBLISH_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Publish' and contains(@class,'Button-module_Button')]"
    )

    PUBLISHED_MARKER = (By.XPATH, "//div[contains(text(),'Collaborative Published Successfully')]")

    # ─── Generic Dropdown Option Pattern ───────────────────────────────────────
    OPTION_BY_VISIBLE_TEXT = "//div[@role='option' and normalize-space(text())='{text}']"
