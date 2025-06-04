class CreateDatasetLocators:
    # ---- Tabs ----
    TAB_METADATA        = "//button[normalize-space()='Metadata']"
    TAB_DATAFILES       = "//button[normalize-space()='Data Files']"
    TAB_PUBLISH         = "//button[normalize-space()='Publish']"

    # ---- Metadata fields ----
    DESCRIPTION         = "//textarea[@name='description']"
    SECTORS_CONTAINER   = "//label[normalize-space()='Sectors']/following::input[1]"
    SECTOR_OPTION       = "//div[@role='option' and normalize-space(.)='{value}']"
    TAGS_CONTAINER      = "//label[normalize-space()='Tags']/following::input[1]"
    TAG_OPTION          = "//div[@role='option' and normalize-space(.)='{value}']"
    GEOGRAPHY_CONTAINER = "//label[normalize-space()='Geography']/following::input[1]"
    GEO_OPTION          = "//div[@role='option' and normalize-space(.)='{value}']"
    # the <input type="date"> immediately after its label
    DATE_CREATED_INPUT = "//label[normalize-space(.)='Date of Creation of Dataset']"\
                         "/following::input[@type='date'][1]"
    SOURCE_INPUT        = "//label[normalize-space()='Source Website']/following::input[1]"
    
    # the <select> for license
    LICENSE_SELECT = "//select[@name='license']"

    # ---- Data Files tab ----
    # grab the file‐picker input anywhere
    DATAFILES_INPUT = "//input[@type='file']"

    # ---- Publish tab ----
    PUBLISH_REVIEW_TEXT = "//h3[contains(normalize-space(.),'REVIEW DATASET DETAILS')]"
    PUBLISH_BUTTON      = "//button[normalize-space()='Publish']"

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
    # Suppose each uploaded row has <td class="uploaded-file-name">sample.csv</td>
    UPLOADED_FILES_NAME_CELLS = "//td[contains(@class,'uploaded-file-name')]"

    # ─── Publish Tab ───────────────────────────────────────────────────────────

    # 7) The main Publish‐tab container (so you know the tab switched)
    # e.g. <div id="publish-tab-content" …>
    PUBLISH_TAB_CONTAINER = "//div[@id='publish-tab-content']"

    # 7b) Once you click “Publish,” the page shows a “Published” badge or text:
    # e.g. <span class="status-badge published">Published</span>
    PUBLISHED_STATUS_BADGE = "//span[contains(@class,'status-badge') and normalize-space(text())='Published']"

    # 7c) The download link (for the newly-published dataset)
    # e.g. <a id="download-dataset" href="...">Download</a>
    DOWNLOAD_LINK = "//a[@id='download-dataset']"