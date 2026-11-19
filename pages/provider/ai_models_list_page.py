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
            message="Timed out waiting for 'Create AI Model' button"
        )
        return True

    def click_add_new_ai_model(self) -> "CreateAiModelPage":
        """Click "Create AI Model"; it creates a draft and opens the Versions step."""
        from pages.provider.create_ai_model_page import CreateAiModelPage

        self.click_until(
            AiModelsLocators.ADD_NEW_AI_MODEL_BTN,
            EC.visibility_of_element_located(AiModelsLocators.ADD_VERSION_BTN),
            message="'Create AI Model' never opened the editor",
        )
        return CreateAiModelPage(self.driver)
