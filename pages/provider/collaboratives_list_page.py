# pages/provider/collaboratives_list_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from pages.provider.create_collaborative_page import CreateCollaborativePage
from locators.provider.collaboratives_list_page_locators import CollaborativesListPageLocators
from locators.provider.create_collaborative_locators import CreateCollaborativeLocators


class CollaborativesListPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver)  # Initialize BasePage with self.wait

    def view_state(self) -> str:
        """'drafts_empty', 'published_empty' or 'rows' (see BasePage.list_view_state)."""
        return self.list_view_state(CollaborativesListPageLocators)

    def is_loaded(self):
        return self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON)
        )

    def click_add_new_collaborative(self):
        """Click "Create Collaborative"; it creates a draft and opens the wizard's About step."""
        self.click_until(
            CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON,
            EC.visibility_of_element_located(CreateCollaborativeLocators.COLLABORATIVE_NAME_INPUT),
            message="'Create Collaborative' never opened the editor",
        )
        return CreateCollaborativePage(self.driver)
