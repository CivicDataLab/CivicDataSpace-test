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

    def is_loaded(self):
        return self.wait_with_timeout(10).until(
            EC.visibility_of_element_located(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON)
        )

    def click_add_new_collaborative(self):
        """
        Click the "Add New Collaborative" button and wait for the create collaborative form to load.

        Returns:
            CreateCollaborativePage instance after the form has loaded
        """
        import time

        # Wait for the button to be clickable before clicking
        button = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable(CollaborativesListPageLocators.ADD_NEW_COLLABORATIVE_BUTTON),
            message="Timed out waiting for 'Add New Collaborative' button to be clickable"
        )
        button.click()

        # Give the modal/form time to appear
        time.sleep(2)

        # Wait for the Collaborative creation form to load by checking for the summary textarea
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located(CreateCollaborativeLocators.COLLABORATIVE_SUMMARY_INPUT),
            message="Timed out waiting for Collaborative creation form to load"
        )

        return CreateCollaborativePage(self.driver)
