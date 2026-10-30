# locators/provider/create_collaborative_locators.py

from selenium.webdriver.common.by import By


def _field_input(label):
    """The input a field label points at (labels carry `for=`; the * is CSS)."""
    return (By.XPATH, f"//input[@id=//label[normalize-space()='{label}']/@for]")


def _field_chips(label):
    return (By.XPATH, f"//input[@id=//label[normalize-space()='{label}']/@for]/preceding-sibling::span//span[@title]")


class CreateCollaborativeLocators:
    """
    The collaborative editor wizard (DataSpaceFrontend#504):
    /collaboratives/edit/<id>/{about,people,content,publish}
    """

    # ─── About ──────────────────────────────────────────────────────────────────
    COLLABORATIVE_NAME_INPUT = (By.XPATH, "//input[@name='title']")
    DESCRIPTION_INPUT = (By.XPATH, "//div[contains(@class, 'ql-editor') and @contenteditable='true']")
    PLATFORM_URL_INPUT = (By.XPATH, "//input[@name='platformUrl']")

    SECTOR_INPUT = _field_input("Sectors")
    SDG_GOALS_INPUT = _field_input("SDG Goals")
    TAGS_INPUT = _field_input("Tags")
    GEOGRAPHY_INPUT = _field_input("Geography")
    # Geography options read "<name> (<parent>)", e.g. "India (Asia Pacific)".
    GEOGRAPHY_OPTION = "//*[@id='{listbox}']//*[@role='option' and starts-with(normalize-space(.), '{name} (')]"
    SECTOR_CHIPS = _field_chips("Sectors")
    SDG_GOALS_CHIPS = _field_chips("SDG Goals")
    TAG_CHIPS = _field_chips("Tags")
    GEOGRAPHY_CHIPS = _field_chips("Geography")

    # Each image field has its own dropzone; the count shifts after an upload,
    # so target by field label, not index.
    COVER_IMAGE_FILE_INPUT = (By.XPATH, "//div[./div/*[normalize-space()='Cover Image']]//input[@type='file']")
    LOGO_FILE_INPUT = (By.XPATH, "//div[./div/*[normalize-space()='Logo']]//input[@type='file']")
    COVER_IMAGE_PREVIEW = (By.XPATH, "//main//img[@alt='Cover Image']")
    LOGO_PREVIEW = (By.XPATH, "//main//img[@alt='Logo']")

    # ─── Content: EntityRowPicker search; results render in a body portal ──────
    DATASET_PICKER_SEARCH = (By.XPATH, "//input[@placeholder='Search published datasets...']")
    USECASE_PICKER_SEARCH = (By.XPATH, "//input[@placeholder='Search published Use Cases...']")
    PICKER_RESULT = (By.XPATH, "//button[contains(@class,'menuItem')]")
    CONNECTED_TITLE = "//section[.//h3[normalize-space()='{heading}']]//*[normalize-space(text())='{title}']"

    # ─── Wizard navigation ──────────────────────────────────────────────────────
    CONTINUE_BUTTON = (By.XPATH, "//button[normalize-space()='Continue']")
    PUBLISH_BUTTON = (By.XPATH, "//button[normalize-space()='Publish Collaborative']")
    PUBLISHED_ROW = "//table//tbody/tr[.//*[contains(normalize-space(),'{name}')]]//*[normalize-space()='Published']"
