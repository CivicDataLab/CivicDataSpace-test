# locators/consumer/locators.py
# Optimized locators with resilient relative XPaths (Phase 13)

from selenium.webdriver.common.by import By

class Locators:
    # ═══════════════════════════════════════════════════════════════════════════
    # Homepage > Home Tab
    # ═══════════════════════════════════════════════════════════════════════════

    ICON                   = (By.XPATH, "//header//nav//img[contains(@src, 'logo') or contains(@class, 'logo')]")
    IMAGE                  = (By.XPATH, "//main//img[contains(@class, 'hero') or contains(@class, 'banner')]")
    SEARCH_BAR             = (By.XPATH, "//input[@type='search' or @placeholder='Search' or contains(@class, 'search')]")
    SEARCH_BUTTON          = (By.XPATH, "//header//nav//button[contains(@aria-label, 'search') or .//span[contains(@class, 'search')]]")
    RECENT_DATASETS_BTN    = (By.XPATH, "//button[contains(., 'Recent') or contains(., 'Datasets')]//span")
    EXPLORE_SECTORS_BTN    = (By.XPATH, "//button[contains(., 'Explore') or contains(., 'Sectors')]//span")

    # Footer elements
    ABOUT_SECTION          = (By.XPATH, "//footer//div[contains(@class, 'about') or .//h3[contains(., 'About')]]")
    SITEMAP_LINKS          = (By.XPATH, "//footer//a[contains(., 'Sitemap')]//span")
    CONTACT_SECTION        = (By.XPATH, "//footer//a[contains(., 'Contact')]//span")

    # Social media icons (footer)
    TWITTER_ICON           = (By.XPATH, "//footer//a[contains(@href, 'twitter')]//svg")
    LINKEDIN_ICON          = (By.XPATH, "//footer//a[contains(@href, 'linkedin')]//svg")
    FACEBOOK_ICON          = (By.XPATH, "//footer//a[contains(@href, 'facebook')]//svg")
    GITHUB_ICON            = (By.XPATH, "//footer//a[contains(@href, 'github')]//svg")
    CDL_REDIRECT_ELEMENT   = (By.XPATH, "//footer//a[contains(@href, 'civicdatalab') or contains(., 'CivicDataLab')]")

    # Mobile navigation
    MOBILE_BURGER_MENU     = (By.XPATH, "//header//nav//button[@aria-label='Menu' or contains(@class, 'menu') or contains(@class, 'burger')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # DATASET TAB
    # ═══════════════════════════════════════════════════════════════════════════

    DATASET_TAB               = (By.XPATH, "//header//nav//a[contains(@href, 'datasets') or contains(., 'Datasets')]")
    DATASET_SEARCH_FIELD      = (By.XPATH, "//input[@type='search' or @placeholder='Search datasets' or contains(@name, 'search')]")
    DATASET_FILTER_RESET_BUTTON = (By.XPATH, "//button[contains(., 'Reset') or contains(., 'Clear')]")
    DATASET_SECTOR_DROPDOWN   = (By.XPATH, "//h3//button[contains(., 'Sector') or preceding-sibling::*[contains(., 'Sector')]]")
    DATASET_TAGS_DROPDOWN     = (By.XPATH, "//h3//button[contains(., 'Tags') or preceding-sibling::*[contains(., 'Tags')]]")
    DATASET_TOGGLE_GRID       = (By.XPATH, "//button[@aria-label='Grid view' or contains(@class, 'grid')]")
    DATASET_TOGGLE_LIST       = (By.XPATH, "//button[@aria-label='List view' or contains(@class, 'list')]")
    DATASET_CARD              = (By.XPATH, "//div[contains(@class, 'dataset-card') or contains(@class, 'DatasetCard')]")
    DATASET_VIEW_DETAILS_LINK = (By.XPATH, "//a[contains(., 'View Details') or contains(., 'Details')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTORS TAB
    # ═══════════════════════════════════════════════════════════════════════════

    SECTORS_TAB          = (By.XPATH, "//header//nav//a[contains(@href, 'sectors') or contains(., 'Sectors')]")
    SECTOR_HEADER        = (By.XPATH, "//main//div[contains(@class, 'header') or .//h1 or .//h2]")
    SECTOR_SEARCH_BAR    = (By.XPATH, "//input[@type='search' or @placeholder='Search sectors']")
    SECTOR_SORT_DROPDOWN = (By.XPATH, "//div[contains(@class, 'sort') or .//select or .//button[contains(., 'Sort')]]")
    SECTOR_CARD          = (By.XPATH, "//div[contains(@class, 'sector-card') or contains(@class, 'SectorCard')]")
    SECTOR_MOBILE_TAB    = (By.XPATH, "//div[@role='dialog' or contains(@class, 'mobile')]//a[contains(., 'Sectors')]")
    SECTOR_SORT_DROPDOWN_MOBILE = (By.XPATH, "//select[contains(@name, 'sort') or contains(@class, 'sort')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # USE CASES TAB
    # ═══════════════════════════════════════════════════════════════════════════

    USE_CASES_TAB    = (By.XPATH, "//header//nav//a[contains(@href, 'usecases') or contains(., 'Use Cases')]")
    USE_CASES_HEADER = (By.XPATH, "//main//span[contains(., 'Use Cases') or contains(., 'UseCases')]")
    USE_CASE_CARD    = (By.XPATH, "//div[contains(@class, 'usecase-card') or contains(@class, 'UseCaseCard')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # ABOUT TAB
    # ═══════════════════════════════════════════════════════════════════════════

    ABOUT_TAB       = (By.XPATH, "//header//nav//a[contains(@href, 'about') or contains(., 'About')]")
    ABOUT_HEADING   = (By.XPATH, "//main//span[contains(., 'About') or preceding::h1[contains(., 'About')]]")
    ABOUT_PARAGRAPH = (By.XPATH, "//main//span[2] | //main//p[contains(@class, 'description')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGIN / SIGN UP (already optimized)
    # ═══════════════════════════════════════════════════════════════════════════

    LOGIN_SIGNUP_LINK    = (By.XPATH, "//a[contains(., 'Login') or contains(., 'Sign Up')]")
    LOGIN_USERNAME_FIELD = (By.XPATH, "//input[@name='username']")
    LOGIN_PASSWORD_FIELD = (By.XPATH, "//input[@name='password']")
