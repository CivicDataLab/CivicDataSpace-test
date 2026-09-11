# locators/provider/create_usecase_locators.py

from selenium.webdriver.common.by import By

class CreateUsecaseLocators:
    """
    All locators for the CreateUsecasePage.
    Keep things as simple constants so that the POM methods can refer to them by name.
    """

    # ─── "Use Case Details" Tab and Fields ─────────────────────────────────────
    DETAILS_TAB = (By.XPATH, "//button[normalize-space()='Use Case Details']")

    USECASE_NAME_INPUT = (By.XPATH, "//div[@class=' pl-2']//button[@type='button']")
    USECASE_SUMMARY_LABEL = (By.XPATH, "//label[normalize-space()='Summary *']")
    # Rich text editor (Quill) - uses contenteditable div, not textarea
    USECASE_SUMMARY_INPUT = (By.XPATH, "//div[contains(@class, 'ql-editor') and @contenteditable='true']")

    PLATFORM_URL_INPUT = (By.XPATH, "//input[@name='platformUrl']")

    TAGS_INPUT = (By.XPATH,"//label[normalize-space()='Tags']/following::input[@role='combobox'][1]")
    TAG_DROPDOWN_ITEM = "//div[@role='option' and normalize-space(.)='{value}']"

    SECTOR_INPUT = (By.XPATH,"//label[normalize-space()='Sectors' or normalize-space()='Sectors *']/following::input[@role='combobox'][1]")
    SECTOR_DROPDOWN_ITEM = "//div[@role='option' and normalize-space(.)='{value}']"

    GEOGRAPHY_CONTAINER = (By.XPATH,"//label[normalize-space()='Geographies' or normalize-space()='Geography *' or normalize-space()='Geography']/following::input[@role='combobox'][1]")
    GEO_OPTION = "//div[@role='option' and starts-with(normalize-space(.), '{value}')]"

    SDG_GOALS_CONTAINER = (By.XPATH,"//label[normalize-space()='SDG Goals *' or normalize-space()='SDG Goal *' or contains(text(),'SDG')]/following::input[@role='combobox'][1]")
    SDG_GOALS_OPTION = "//div[@role='option' and normalize-space(.)='{value}']"

    STARTED_ON_INPUT = (By.XPATH, "//input[@type='date' and @name='startedOn']")

    RUNNING_STATUS_INPUT = (By.XPATH, "//select[@name='runningStatus']")
    RUNNING_STATUS_DROP_ITEM = "//select[@name='runningStatus']/option[normalize-space()='{status_text}']"

    COMPLETED_ON_INPUT = (By.XPATH, "//input[@type='date' and @name='completedOn']")

    LOGO_UPLOAD_INPUT = (By.XPATH, "//div[contains(@class,'FileUpload-module_Action')]")

    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    # Rich text editor (Quill) - uses contenteditable div, not textarea
    SUMMARY_INPUT = (By.XPATH, "//div[contains(@class, 'ql-editor') and @contenteditable='true']")
    STARTED_ON_VALUE_INPUT = (By.XPATH, "//input[@type='date' and @name='startedOn']")
    COMPLETED_ON_VALUE_INPUT = (By.XPATH, "//input[normalize-space(.)='Completed On']")
    RUNNING_STATUS_SELECT = (By.XPATH, "//select[@name='runningStatus']")

    # ─── Tags / Sectors / SDG Goals Chips (Assertions) ─────────────────────────
    SELECTED_TAGS = "//label[normalize-space()='Tags']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_SECTORS = "//label[normalize-space()='Sectors' or normalize-space()='Sectors *']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_GEOGRAPHY = "//label[normalize-space(text())='Geographies' or normalize-space(text())='Geography *' or normalize-space(text())='Geography']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_SDG_GOALS = "//label[normalize-space()='SDG Goals *' or normalize-space()='SDG Goal *' or contains(normalize-space(),'SDG')]/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"

    # ─── Logo Preview (Post-upload Check) ──────────────────────────────────────
    LOGO_PREVIEW = (By.CSS_SELECTOR, ".uploaded-logo-preview")

    # ─── "Datasets" Tab ────────────────────────────────────────────────────────
    DATASETS_TAB = (By.XPATH, "//button[normalize-space()='Datasets']")
    FIRST_DATASET_CHECKBOX = (By.XPATH, "//tbody/tr[1]//button[@role='checkbox']")
    SELECTED_DATASET_CHECKBOX = (By.XPATH, "//tbody/tr[1]//button[@data-state='checked' and @aria-checked='true']")
    SUBMIT_DATASETS_BUTTON = (By.XPATH, "//button[normalize-space()='Submit']")

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

    # ─── Wizard Navigation ──────────────────────────────────────────────────────
    NEXT_BUTTON = (By.XPATH, "//button[normalize-space()='Next']")

    # ─── "Publish" Tab ─────────────────────────────────────────────────────────
    # Publish navigation TAB — must be a sibling of "Contributors" tab to avoid matching content buttons
    PUBLISH_TAB = (By.XPATH, "//button[normalize-space()='Publish' and preceding-sibling::button[normalize-space()='Contributors']]")
    # Publish action BUTTON — has Button-module class (distinct from the tab nav button)
    PUBLISH_BUTTON = (By.XPATH, "//button[normalize-space()='Publish' and contains(@class,'Button-module_Button')]")

    PUBLISHED_MARKER = (By.XPATH, "//*[contains(.,'UseCase Published Successfully')]")

    # ─── Generic Dropdown Option Pattern ───────────────────────────────────────
    OPTION_BY_VISIBLE_TEXT = "//div[@role='option' and normalize-space(text())='{text}']"
