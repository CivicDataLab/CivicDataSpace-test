# pages/provider/members_page.py

import time

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from locators.provider.members_locators import MembersLocators as L
from pages.base_page import BasePage


class MembersPage(BasePage):
    """An organization's "Admin & Members" page. Actions only; the tests assert."""

    def open(self) -> "MembersPage":
        """Open the page from the organization dashboard's sidebar."""
        link = self.wait_with_timeout(20).until(
            EC.presence_of_element_located(L.SIDEBAR_LINK), message="No 'Admin & Members' link in the dashboard sidebar"
        )
        self.driver.execute_script("arguments[0].click();", link)
        self.wait_with_timeout(20).until(
            EC.visibility_of_element_located(L.HEADING), message="The 'Admin & Members' page never opened"
        )
        return self

    def rows(self) -> list[dict]:
        """Visible members as {'email', 'role', 'actions': [button labels]}."""
        try:
            out = []
            for row in self.driver.find_elements(*L.ROWS):
                cells = [c.text.strip() for c in row.find_elements(By.XPATH, L.ROW_CELLS)]
                actions = [b.get_attribute("textContent").strip() for b in row.find_elements(By.XPATH, L.ROW_ACTIONS)]
                email = next((c for c in cells if "@" in c), "")
                out.append({"email": (email.splitlines() or [""])[-1].strip(), "role": cells[2] if len(cells) > 2 else "",
                            "actions": actions})
            return out
        except StaleElementReferenceException:  # the table re-rendered while reading
            return self.rows()

    def wait_for_rows(self, count: int) -> list[dict]:
        """Wait until `count` members are listed with their actions rendered."""
        def check(d):
            rows = self.rows()
            return rows if len(rows) == count and all(r["actions"] for r in rows) else False

        return self.wait_with_timeout(30).until(
            check, message=f"The members table never listed {count} members: {self.rows()}"
        )

    # ─── Add, edit and remove ───────────────────────────────────────────────────

    def toast_shown(self, text: str, timeout: int = 10) -> bool:
        try:
            self.wait_with_timeout(timeout).until(EC.visibility_of_element_located((By.XPATH, L.TOAST.format(text=text))))
            return True
        except TimeoutException:
            return False

    def open_add_dialog(self):
        self.click_until(L.ADD_BUTTON, EC.visibility_of_element_located(L.USER_INPUT), message="Add Member never opened its dialog")
        return self

    def dialog_title(self) -> str:
        return self.find(L.DIALOG_TITLE).text.strip()

    def pick_user(self, search: str, full_name: str):
        """Type into 'Select user' and click the suggestion called `full_name`.

        The list is fetched with the text as it stood one keystroke earlier, so
        an extra character makes it match the whole of `search`.
        """
        box = self.wait.until(EC.element_to_be_clickable(L.USER_INPUT))
        box.click()
        box.send_keys(search)
        time.sleep(1.5)  # let the typed text settle, or the extra character reuses the stale one
        box.send_keys("x")
        self.wait_with_timeout(20).until(
            EC.element_to_be_clickable((By.XPATH, L.USER_OPTION.format(name=full_name))),
            message=f"No user called {full_name!r} was offered for {search!r}",
        ).click()
        return self

    def pick_role(self, role: str):
        trigger = self.wait.until(EC.element_to_be_clickable(L.ROLE_SELECT))
        trigger.click()
        listbox = self.wait.until(lambda d: trigger.get_attribute("aria-controls") or False)
        self.wait_with_timeout(15).until(
            EC.element_to_be_clickable((By.XPATH, L.ROLE_OPTION.format(listbox=listbox, role=role))),
            message=f"No {role!r} role was offered",
        ).click()
        self.wait_with_timeout(10).until(lambda d: role in trigger.text, message=f"The role select never showed {role!r}")
        return self

    def role_options(self) -> list[str]:
        trigger = self.wait.until(EC.element_to_be_clickable(L.ROLE_SELECT))
        trigger.click()
        listbox = self.wait.until(lambda d: trigger.get_attribute("aria-controls") or False)
        options = self.wait_with_timeout(15).until(
            lambda d: d.find_elements(By.XPATH, f"//*[@id='{listbox}']//*[@role='option']") or False)
        names = [o.get_attribute("textContent").strip() for o in options]
        trigger.send_keys("\ue00c")  # Escape
        return names

    def is_submit_enabled(self, label: str) -> bool:
        btn = self.find((By.XPATH, L.SUBMIT.format(label=label)))
        return btn.is_enabled() and btn.get_attribute("aria-disabled") != "true"

    def submit(self, label: str):
        """Press Add or Update and wait for the dialog to close."""
        self.click_until((By.XPATH, L.SUBMIT.format(label=label)), EC.invisibility_of_element_located(L.USER_INPUT),
                         message=f"The dialog stayed open after '{label}'")
        return self

    def row_action(self, email: str, action: str):
        """Press a row's icon button; `action` is its hidden label ('Edit', 'Remove member')."""
        self.click_until((By.XPATH, L.ROW_ACTION.format(email=email, action=action)),
                         lambda d: True, message=f"No '{action}' button on the row of {email}")
        return self

    def answer_alert(self, label: str):
        self.click_until((By.XPATH, L.ALERT_BUTTON.format(label=label)), EC.invisibility_of_element_located(L.ALERT),
                         message=f"The confirm stayed open after '{label}'")
        return self

    def alert_title(self) -> str:
        return self.wait_with_timeout(10).until(EC.visibility_of_element_located(L.ALERT_TITLE)).text.strip()
