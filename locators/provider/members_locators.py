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

    ADD_BUTTON = (By.XPATH, "//main//button[normalize-space()='Add Member']")
    DIALOG = (By.XPATH, "//*[@role='dialog']")
    DIALOG_TITLE = (By.XPATH, "//*[@role='dialog']//h2[contains(@class,'headingLg')]")
    USER_INPUT = (By.XPATH, "//*[@role='dialog']//input[@id='combobox']")
    USER_OPTION = "//*[@role='dialog']//div[contains(@class,'cursor-pointer') and normalize-space()='{name}']"
    ROLE_SELECT = (By.XPATH, "//*[@role='dialog']//button[@id=//label[normalize-space()='Select a role *']/@for]")
    ROLE_OPTION = "//*[@id='{listbox}']//*[@role='option' and normalize-space()='{role}']"
    SUBMIT = "//*[@role='dialog']//button[normalize-space()='{label}']"
    ROW_BY_EMAIL = "//main//table//tbody/tr[.//td[contains(normalize-space(),'{email}')]]"
    ROW_ACTION = ROW_BY_EMAIL + "//td[last()]//button[contains(normalize-space(.),'{action}')]"
    ALERT = (By.XPATH, "//*[@role='alertdialog']")
    ALERT_TITLE = (By.XPATH, "//*[@role='alertdialog']//h2")
    ALERT_BUTTON = "//*[@role='alertdialog']//button[normalize-space()='{label}']"
    TOAST = "//*[normalize-space(text())='{text}']"
