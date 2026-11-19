# locators/provider/members_locators.py
#
# The organization's "Admin & Members" page (DataSpaceFrontend#547): one row
# per member with name, e-mail, role, date joined and icon-only row actions
# whose labels ("Edit <name>", "Remove member") are visually hidden text.

from selenium.webdriver.common.by import By


class MembersLocators:
    SIDEBAR_LINK = (By.XPATH, "//aside//nav//a[.//span[normalize-space()='Admin & Members']]")
    HEADING = (By.XPATH, "//main//h2[normalize-space()='Admin & Members']")

    ROWS = (By.XPATH, "//main//table//tbody/tr[td[not(contains(@class,'EmptyCell'))]]")
    ROW_CELLS = ".//td"
    ROW_ACTIONS = ".//td[last()]//button"
