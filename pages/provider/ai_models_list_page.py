# pages/provider/ai_models_list_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from locators.provider.ai_models_locators import AiModelsLocators


class AiModelsListPage(BasePage):
    """POM for the AI Models list page (/dashboard/self/.../aimodels)."""

    def is_loaded(self) -> bool:
        self.wait_with_timeout(15).until(
            EC.presence_of_element_located(AiModelsLocators.ADD_NEW_AI_MODEL_BTN),
            message="Timed out waiting for 'Add New AI Model' button"
        )
        return True

    def click_add_new_ai_model(self) -> "CreateAiModelPage":
        from pages.provider.create_ai_model_page import CreateAiModelPage

        btn = self.wait_with_timeout(15).until(
            EC.presence_of_element_located(AiModelsLocators.ADD_NEW_AI_MODEL_BTN),
            message="Timed out waiting for 'Add New AI Model' button"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)

        # The button creates the model immediately and navigates to the editor
        self.wait_with_timeout(20).until(
            lambda d: '/aimodels/edit/' in d.current_url,
            message="Timed out waiting for AI model editor URL"
        )

        # Wait for the Metadata tab to confirm the editor has loaded
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.TAB_METADATA)),
            message="Timed out waiting for Metadata tab in AI model editor"
        )

        return CreateAiModelPage(self.driver)
