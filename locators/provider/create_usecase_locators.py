# locators/provider/create_usecase_locators.py

from selenium.webdriver.common.by import By

class CreateUsecaseLocators:
    """
    All locators for the CreateUsecasePage.
    Keep things as simple constants so that the POM methods can refer to them by name.
    """

    # ─── “Use Case Details” Tab and Fields ─────────────────────────────────────
    DETAILS_TAB = (By.XPATH, "//button[normalize-space()='Use Case Details']")

    USECASE_NAME_INPUT = (By.XPATH, "//div[@class=' pl-2']//button[@type='button']")
    USECASE_SUMMARY_INPUT = (By.XPATH, "//textarea[@name='summary']")

    TAGS_INPUT = (By.XPATH,"//label[normalize-space()='Tags']/following::input[@role='combobox'][1]")
    TAG_DROPDOWN_ITEM = "//div[@role='option' and normalize-space(.)='{value}']"

    SECTOR_INPUT = (By.XPATH,"//label[normalize-space()='Sectors *']/following::input[@role='combobox'][1]")
    SECTOR_DROPDOWN_ITEM = "//div[@role='option'][normalize-space(.)='{value}']"

    GEOGRAPHY_CONTAINER = (By.XPATH,"//label[normalize-space()='Geography *']/following::input[1]")
    GEO_OPTION = "//div[@role='option' and normalize-space(.)='{value}']"

    SDG_GOALS_CONTAINER = (By.XPATH,"//label[normalize-space()='SDG Goal *']/following::input[1]")
    SDG_GOALS_OPTION = "//div[@role='option' and normalize-space(.)='{value}']"

    STARTED_ON_INPUT = (By.XPATH, "//input[@type='date' and @name='startedOn']")

    RUNNING_STATUS_COMBO = (By.XPATH, "//select[@name='runningStatus']")

    COMPLETED_ON_INPUT = (By.XPATH, "//input[@type='date' and @name='completedOn']")

    LOGO_UPLOAD_INPUT = (By.XPATH, "//div[@class='FileUpload-module_Action__Hg0nE']")

    # ─── Fields Used for Value Retrieval / Assertions ──────────────────────────
    SUMMARY_INPUT = (By.XPATH, "//textarea[@name='summary']")
    STARTED_ON_VALUE_INPUT = (By.XPATH, "//input[@type='date' and @name='startedOn']")
    COMPLETED_ON_VALUE_INPUT = (By.XPATH, "//input[normalize-space(.)='Completed On']")
    RUNNING_STATUS_SELECT = (By.XPATH, "//select[@name='runningStatus']")

    # ─── Tags / Sectors / SDG Goals Chips (Assertions) ─────────────────────────
    SELECTED_TAGS = "//div[contains(@class,'Input-module_tags')]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_SECTORS = "//div[contains(@class,'Input-module_tags')]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_GEOGRAPHY = "//label[normalize-space(text())='Geography *']/following::div[contains(@class,'Input-module_tags')][1]//span[contains(@class,'Tag-module_TagText')]"
    SELECTED_SDG_GOALS = "//div[contains(@class,'Input-module_tags')]//span[contains(@class,'Tag-module_TagText')]"

    # ─── Logo Preview (Post-upload Check) ──────────────────────────────────────
    LOGO_PREVIEW = (By.CSS_SELECTOR, ".uploaded-logo-preview")

    # ─── “Datasets” Tab ────────────────────────────────────────────────────────
    DATASETS_TAB = (By.XPATH, "//button[normalize-space()='Datasets']")
    FIRST_DATASET_CHECKBOX = (By.XPATH, "(//table//input[@type='checkbox'])[1]")
    SELECTED_DATASET_CHECKBOXES = (By.XPATH, '//input[@type="checkbox" and @checked]')
    SUBMIT_DATASETS_BUTTON = (By.XPATH, "//button[normalize-space()='Submit']")

    # ─── “Contributors” Tab ────────────────────────────────────────────────────
    CONTRIBUTORS_TAB = (By.XPATH, "//button[normalize-space()='Contributors']")
    CONTRIBUTORS_INPUT = (By.XPATH, "//input[@placeholder='Add Contributors']")
    SUPPORTERS_INPUT = (By.XPATH, "//input[@placeholder='Add Supporters']")
    PARTNERS_INPUT = (By.XPATH, "//input[@placeholder='Add Partners']")

    # ─── Contributors/Sponsors List Items ──────────────────────────────────────
    CONTRIBUTORS_LIST_ITEMS = (By.CSS_SELECTOR, ".contributors-list-item")
    SUPPORTERS_LIST_ITEMS = (By.CSS_SELECTOR, ".supporters-list-item")
    PARTNERS_LIST_ITEMS = (By.CSS_SELECTOR, ".partners-list-item")

    # ─── “Publish” Tab ─────────────────────────────────────────────────────────
    PUBLISH_TAB = (By.XPATH, "//button[normalize-space()='Publish']")
    PUBLISH_BUTTON = (By.XPATH, "//button[normalize-space()='Publish' and not(@disabled)]")
    PUBLISHED_MARKER = (By.XPATH, "//div[contains(text(),'Published')]")

    # ─── Generic Dropdown Option Pattern ───────────────────────────────────────
    OPTION_BY_VISIBLE_TEXT = "//div[@role='option' and normalize-space(text())='{text}']"
