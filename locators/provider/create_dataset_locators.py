class CreateDatasetLocators:
    # ---- Tabs ----
    TAB_METADATA        = "//button[normalize-space()='Metadata']"
    TAB_DATAFILES       = "//button[normalize-space()='Data Files']"
    TAB_PUBLISH         = "//button[normalize-space()='Publish']"

    # ---- Metadata fields ----
    DESCRIPTION         = "//textarea[@name='description']"

    SECTOR_INPUT        = "//label[normalize-space()='Sectors *']/following::input[@role='combobox'][1]"
    SECTOR_DROPDOWN_ITEM = "//div[@role='option'][normalize-space(.)='{value}']"

    TAGS_INPUT           = "//label[normalize-space()='Tags *']/following::input[@role='combobox'][1]"
    TAG_DROPDOWN_ITEM    = "//div[@role='option' and normalize-space(.)='{value}']"

    GEOGRAPHY_CONTAINER = "//label[normalize-space()='Geography']/following::input[1]"
    GEO_OPTION          = "//div[@role='option' and normalize-space(.)='{value}']"

    DATE_CREATED_INPUT = "//label[normalize-space(.)='Date of Creation of Dataset']"\
                         "/following::input[@type='date'][1]"

    SOURCE_INPUT        = "//label[normalize-space()='Source Website']/following::input[1]"
    
    # the <select> for license
    LICENSE_SELECT = "//select[@name='license']"

    # ---- Data Files tab ----
    # grab the file‐picker input anywhere
    DATAFILES_INPUT = "//input[@type='file']"

    BACK_BUTTON = "//*[contains(@class,'tabler-icon-arrow-left')]/ancestor::button[1]"

    # ---- Publish tab ----
    PUBLISH_REVIEW_TEXT = "//span[normalize-space()='REVIEW DATASET DETAILS']"
    PUBLISH_BUTTON      = "//span[@class='Button-module_removeUnderline__dq0ct'][normalize-space()='Publish']"

    #Getter locators :
    # 5b) After selecting sectors, each chosen sector usually appears as a "pill"
    SECTOR_SELECTED_PILL = (
        "//div[contains(@class,'Input-module_tags')]"
        "//span[contains(@class,'Tag-module_TagText')]"
    )
    # 5c) Tag pills (after selecting tags, each chosen tag appears)
    TAG_SELECTED_PILL = (
        "//div[contains(@class,'Input-module_tags')]"
        "//span[contains(@class,'Tag-module_TagText')]"
    )
    # 5d) Selected geography appears as a single “pill” or dropdown value
    GEOGRAPHY_SELECTED_PILL = (
        "//label[normalize-space(text())='Geography']"
        "/following::div[contains(@class,'Input-module_tags')][1]"
        "//span[contains(@class,'Tag-module_TagText')]"
    )

    # 5e) Date of Creation input (<input type="date">)
    GET_DATE_CREATED = "//label[normalize-space(.)='Date of Creation of Dataset']"\
                         "/following::input[@type='date'][1]"

    # 5f) Source website input field
    SOURCE_WEBSITE_INPUT = "//label[normalize-space()='Source Website']/following::input[1]"

    # 5g) License dropdown (container that shows the currently selected license)
    LICENSE_SELECTED_TEXT = (
        "//div[contains(@class,'Labelled-module_LabelWrapper')"
        "    and .//label[normalize-space(text())='License']]"
        "/following-sibling::div//span[contains(@class,'Select-module_SelectedOption__')]"
    )


    # ─── Data Files Tab ────────────────────────────────────────────────────────

    # 6b) After uploading, you want a list of filenames.

    # the table itself (you can narrow this down if you have a more specific container)
    DATAFILES_TABLE = "//div[contains(@class,'opub-DataTable')]//table"

    # all of the “Name of Resource” cells in its first column
    RESOURCE_NAME_CELLS = DATAFILES_TABLE + "/tbody/tr/td[1]//div"

    # ─── Publish Tab ───────────────────────────────────────────────────────────

    # 7) The main Publish‐tab container (so you know the tab switched)
    # e.g. <div id="publish-tab-content" …>
    PUBLISH_TAB_CONTAINER = "//div[@class=' w-full py-6']"

    # 7b) Once you click “Publish,” the page shows a “Published” badge or text:
    # e.g. <span class="status-badge published">Published</span>
    PUBLISHED_STATUS_BADGE = "//span[contains(@class,'status-badge') and normalize-space(text())='Published']"

    # 7c) The download link (for the newly-published dataset)
    # e.g. <a id="download-dataset" href="...">Download</a>
    DOWNLOAD_LINK = "//a[@id='download-dataset']"