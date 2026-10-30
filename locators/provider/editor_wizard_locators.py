# locators/provider/editor_wizard_locators.py
#
# The step-by-step editor shared by use cases, collaboratives and other
# entities since DataSpaceFrontend#470/#504: a Progress nav, autosaving fields,
# and Continue / Publish <Entity> buttons.

from selenium.webdriver.common.by import By


class EditorWizardLocators:
    # Field labels carry `for=` (the required * is CSS, not text).
    FIELD_INPUT = "//input[@id=//label[normalize-space()='{label}']/@for]"
    FIELD_CHIPS = FIELD_INPUT + "/preceding-sibling::span//span[@title]"

    # A button-style select (Radix) names its options' container in aria-controls.
    SELECT_BY_LABEL = "//button[@id=//label[normalize-space()='{label}']/@for]"
    SELECT_OPTION = "//*[@id='{listbox}']//*[@role='option' and normalize-space()='{text}']"
    LISTBOX_OPTIONS = "//*[@id='{listbox}']//*[@role='option']"

    # Geography options read "<name> (<parent>)", e.g. "India (Asia Pacific)".
    GEOGRAPHY_OPTION = "//*[@id='{listbox}']//*[@role='option' and starts-with(normalize-space(.), '{name} (')]"

    # Each image field has its own dropzone. The number of file inputs shifts
    # after an upload, so address them by field label, not index. Match the label
    # exactly (a required one renders as "Thumbnail*"): a prefix match also hits
    # the wrapper around several image fields.
    IMAGE_FILE_INPUT = "//div[./div/*[normalize-space()='{label}' or normalize-space()='{label}*']]//input[@type='file']"
    IMAGE_PREVIEW = "//main//img[@alt='{label}']"

    # EntityRowPicker: a search box whose results render in a body portal.
    PICKER_SEARCH = "//input[@placeholder='{placeholder}']"
    PICKER_RESULT = (By.XPATH, "//button[contains(@class,'entity-row-picker') and contains(@class,'menuItem')]")
    CONNECTED_TITLE = "//section[.//h3[starts-with(normalize-space(),'{heading}')]]//*[normalize-space(text())='{title}']"

    CONTINUE_BUTTON = (By.XPATH, "//button[normalize-space()='Continue']")
    PUBLISH_BUTTON = "//button[normalize-space()='Publish {entity}']"
    PUBLISHED_ROW = "//table//tbody/tr[.//*[contains(normalize-space(),'{name}')]]//*[normalize-space()='Published']"
