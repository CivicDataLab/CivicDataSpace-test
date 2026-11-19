# pages/provider/members_page.py

from selenium.common.exceptions import StaleElementReferenceException
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
                out.append({"email": email.splitlines()[-1].strip(), "role": cells[2] if len(cells) > 2 else "",
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
