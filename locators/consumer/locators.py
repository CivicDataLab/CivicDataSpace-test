# locators.py

class Locators:
    # Homepage > Home Tab
    ICON                   = "/html/body/main/div/header/nav/div/div[1]/a/div/div/div[1]/img"
    IMAGE                  = "/html/body/main/div/div/main/div/div[2]/img"
    SEARCH_BAR             = "/html/body/main/div/div/main/div/div[1]/div[2]/div/div/div/div/div"
    SEARCH_BUTTON          = "/html/body/main/div/header/nav/div/div[2]/div[1]/span/button/span[2]"
    RECENT_DATASETS_BTN    = "/html/body/main/div/div/div[1]/div[1]/div/button/span/span"
    EXPLORE_SECTORS_BTN    = "/html/body/main/div/div/div[2]/div[1]/div/button/span/span"
    ABOUT_SECTION          = "/html/body/main/div/footer/div/div"
    SITEMAP_LINKS          = "/html/body/main/div/footer/div/div/div[2]/div[1]/a[2]/span"
    CONTACT_SECTION        = "/html/body/main/div/footer/div/div/div[2]/div[1]/a[3]/span"
    TWITTER_ICON           = "/html/body/main/div/footer/div/div/div[1]/div[2]/div[2]/div[1]/span/svg"
    LINKEDIN_ICON          = "/html/body/main/div/footer/div/div/div[1]/div[2]/div[2]/div[2]/span/svg"
    FACEBOOK_ICON          = "/html/body/main/div/footer/div/div/div[1]/div[2]/div[2]/div[3]/span/svg"
    GITHUB_ICON            = "/html/body/main/div/footer/div/div/div[1]/div[2]/div[2]/div[4]/span/svg"
    CDL_REDIRECT_ELEMENT   = "/html/body/main/div/footer/div/div/div[2]/div[2]/a"
    MOBILE_BURGER_MENU     = "/html/body/main/div/header/nav/div/div[1]/div/button"

    # ─── DATASET TAB ────────────────────────────────────────────────────────────
    DATASET_TAB               = "/html/body/main/div/header/nav/div/div[2]/div[2]/div[1]/a"
    DATASET_SEARCH_FIELD      = "/html/body/main/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div/div/div[2]/div/div/input"
    DATASET_FILTER_RESET_BUTTON     = "/html/body/main/div/div/div[2]/div/div/div[1]/div/div[1]/div/div[2]/button"
    DATASET_SECTOR_DROPDOWN   = "/html/body/main/div/div/div[2]/div/div/div[1]/div/div[2]/div[1]/div/div/h3/button"
    DATASET_TAGS_DROPDOWN     = "/html/body/main/div/div/div[2]/div/div/div[1]/div/div[2]/div[2]/div/div/h3/button"
    DATASET_TOGGLE_GRID       = "/html/body/main/div/div/div[2]/div/div/div[2]/div[1]/div[2]/div[1]/div/div[1]/button"
    DATASET_TOGGLE_LIST       = "/html/body/main/div/div/div[2]/div/div/div[2]/div[1]/div[2]/div[1]/div/div[2]/button"
    DATASET_CARD              = "/html/body/main/div/div/div[2]/div/div/div[2]/div[2]/div[1]"
    DATASET_VIEW_DETAILS_LINK = "/html/body/main/div/div/div[2]/div/div/div[2]/div[2]/div[1]/a[1]"

    # ─── SECTORS TAB ────────────────────────────────────────────────────────────
    SECTORS_TAB          = "/html/body/main/div/header/nav/div/div[2]/div[2]/div[2]/a"
    SECTOR_HEADER        = "/html/body/main/div/main/div[2]/div[1]/div/div[1]"
    SECTOR_SEARCH_BAR    = "/html/body/main/div/main/div[2]/div[2]/div[1]/div/div[1]/div/div/div/div"
    SECTOR_SORT_DROPDOWN = "/html/body/main/div/main/div[2]/div[2]/div[1]/div/div[2]/div/div"
    SECTOR_CARD          = "/html/body/main/div/main/div[2]/div[2]/div[2]"
    SECTOR_MOBILE_TAB    = "/html/body/div[2]/div/div[1]/div[2]/a"
    SECTOR_SORT_DROPDOWN_MOBILE = "/html/body/main/div/main/div[2]/div[2]/div[1]/div/div[2]/div/div/select"

    # ─── USE CASES TAB ──────────────────────────────────────────────────────────
    USE_CASES_TAB    = "/html/body/main/div/header/nav/div/div[2]/div[2]/div[3]/a"
    USE_CASES_HEADER = "/html/body/main/div/main/div[2]/div/div/span[1]"
    USE_CASE_CARD    = "/html/body/main/div/main/div[3]/div[2]"

    # ─── ABOUT TAB ─────────────────────────────────────────────────────────────
    ABOUT_TAB       = "/html/body/main/div/header/nav/div/div[2]/div[2]/div[4]/a"
    ABOUT_HEADING   = "/html/body/main/div/main/div[2]/div/div/span[1]"
    ABOUT_PARAGRAPH = "/html/body/main/div/main/div[2]/div/div/span[2]"

    # ─── LOGIN / SIGN UP ────────────────────────────────────────────────────────
    LOGIN_SIGNUP_LINK    = "//a[contains(., 'Login') or contains(., 'Sign Up')]"
    LOGIN_USERNAME_FIELD = "//input[@name='username']"
    LOGIN_PASSWORD_FIELD = "//input[@name='password']"