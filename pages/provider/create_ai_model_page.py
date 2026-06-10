# pages/provider/create_ai_model_page.py

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage
from locators.provider.ai_models_locators import AiModelsLocators


class CreateAiModelPage(BasePage):
    """POM for the three-tab AI model editor (Metadata / Version / Publish)."""

    # ── Tab navigation ────────────────────────────────────────────────────────

    def go_to_metadata_tab(self) -> "CreateAiModelPage":
        tab = self.wait_with_timeout(10).until(
            EC.presence_of_element_located((By.XPATH, AiModelsLocators.TAB_METADATA))
        )
        self.driver.execute_script("arguments[0].click();", tab)
        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.DESCRIPTION_EDITOR))
        )
        return self

    def go_to_version_tab(self) -> "CreateAiModelPage":
        # "Next" advances and saves the current step; fall back to tab click if absent.
        try:
            btn = self.wait_with_timeout(5).until(
                EC.element_to_be_clickable((By.XPATH, AiModelsLocators.WIZARD_NEXT_BTN))
            )
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.5)
        except TimeoutException:
            tab = self.wait_with_timeout(10).until(
                EC.presence_of_element_located((By.XPATH, AiModelsLocators.TAB_VERSION))
            )
            self.driver.execute_script("arguments[0].click();", tab)
        return self

    def go_to_publish_tab(self) -> "CreateAiModelPage":
        # "Next" advances and saves the current step; fall back to tab click if absent.
        try:
            btn = self.wait_with_timeout(5).until(
                EC.element_to_be_clickable((By.XPATH, AiModelsLocators.WIZARD_NEXT_BTN))
            )
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.5)
        except TimeoutException:
            tab = self.wait_with_timeout(10).until(
                EC.presence_of_element_located((By.XPATH, AiModelsLocators.TAB_PUBLISH))
            )
            self.driver.execute_script("arguments[0].click();", tab)

        self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.PUBLISH_REVIEW_SECTION))
        )

        # Wizard navigation reads from a stale React Query cache populated at creation
        # (all fields empty). Refresh forces a server refetch so the validator sees the
        # autosaved data and clears the "fields missing" error.
        self.driver.refresh()
        self.wait_with_timeout(15).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.PUBLISH_REVIEW_SECTION))
        )
        return self

    # ── Metadata – access type (must be set before any other save fires) ──────

    def ensure_open_access(self) -> "CreateAiModelPage":
        # New models are created with isPublic=False. The useEffect([model])
        # then sets formData.accessType='restricted', and handleSave() has an
        # early-return guard: if accessType !== 'open' → no mutation fires.
        # Clicking the Open Access checkbox always calls
        # handleSave({...formData, accessType:'open'}), bypassing the guard,
        # which saves isPublic=true to the server and resets the cascade.
        loc = (By.XPATH, AiModelsLocators.OPEN_ACCESS_CHECKBOX)
        el = self.wait_with_timeout(10).until(EC.presence_of_element_located(loc))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", el)
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    # ── Metadata – text inputs ────────────────────────────────────────────────

    def enter_description(self, text: str) -> "CreateAiModelPage":
        editor = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, AiModelsLocators.DESCRIPTION_EDITOR))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", editor)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", editor)
        editor.send_keys(Keys.CONTROL + "a")
        editor.send_keys(Keys.DELETE)
        editor.send_keys(text)
        # send_keys triggers Quill text-change → React onChange → setFormData queued.
        # Wait for React to commit that microtask before blurring, otherwise onBlur
        # fires handleSave() with stale formData.description === ''.
        time.sleep(0.5)
        self.driver.execute_script("arguments[0].blur();", editor)
        time.sleep(0.3)
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    def _fill_textarea(self, locator, text: str):
        el = self.wait_with_timeout(10).until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        # Step 1: set value and dispatch input/change → React onChange queues state update
        self.driver.execute_script(
            """
            const el = arguments[0], val = arguments[1];
            el.focus();
            const setter = Object.getOwnPropertyDescriptor(
                HTMLTextAreaElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            el, text
        )
        # Step 2: wait for React to commit the queued state update before blurring,
        # otherwise onBlur fires handleSave() with stale formData (empty value).
        time.sleep(0.5)
        # Step 3: blur to trigger onBlur → handleSave() with updated formData
        self.driver.execute_script(
            """
            const el = arguments[0];
            el.blur();
            el.dispatchEvent(new Event('focusout', {bubbles: true}));
            """,
            el
        )
        time.sleep(0.3)
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return el

    def enter_target_users(self, text: str) -> "CreateAiModelPage":
        self._fill_textarea((By.XPATH, AiModelsLocators.TARGET_USERS_INPUT), text)
        return self

    def enter_intended_use(self, text: str) -> "CreateAiModelPage":
        self._fill_textarea((By.XPATH, AiModelsLocators.INTENDED_USE_INPUT), text)
        return self

    def enter_model_website(self, url: str) -> "CreateAiModelPage":
        loc = (By.XPATH, AiModelsLocators.MODEL_WEBSITE_INPUT)
        el = self.wait_with_timeout(10).until(EC.presence_of_element_located(loc))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        # Step 1: set value + fire input/change → React onChange queues state update
        self.driver.execute_script(
            """
            const el = arguments[0], val = arguments[1];
            el.focus();
            const setter = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            el, url
        )
        # Step 2: let React commit before blurring (handleWebsiteBlur reads formData.modelWebsite)
        time.sleep(0.5)
        # Step 3: blur → handleWebsiteBlur → handleSave() with updated modelWebsite
        self.driver.execute_script(
            """
            const el = arguments[0];
            el.blur();
            el.dispatchEvent(new Event('focusout', {bubbles: true}));
            """,
            el
        )
        time.sleep(0.3)
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    # ── Metadata – native <select> fields ─────────────────────────────────────

    def select_model_type(self, value: str) -> "CreateAiModelPage":
        self.set_react_select_by_text(
            (By.XPATH, AiModelsLocators.MODEL_TYPE_SELECT), value
        )
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    def select_max_tokens(self, value: str) -> "CreateAiModelPage":
        self.set_react_select_by_text(
            (By.XPATH, AiModelsLocators.MAX_TOKENS_SELECT), value
        )
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    def select_usage_license(self, value: str) -> "CreateAiModelPage":
        self.set_react_select_by_text(
            (By.XPATH, AiModelsLocators.USAGE_LICENSE_SELECT), value
        )
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    # ── Metadata – custom combobox fields ─────────────────────────────────────

    def select_sectors(self, items: list) -> "CreateAiModelPage":
        loc = (By.XPATH, AiModelsLocators.SECTORS_INPUT)
        for val in items:
            self._scroll_and_select(loc, val)
        return self

    def select_tags(self, items: list) -> "CreateAiModelPage":
        loc = (By.XPATH, AiModelsLocators.TAGS_INPUT)
        for val in items:
            self._scroll_and_select(loc, val)
        return self

    def select_languages(self, items: list) -> "CreateAiModelPage":
        loc = (By.XPATH, AiModelsLocators.LANGUAGES_INPUT)
        for val in items:
            self._scroll_and_select(loc, val)
        return self

    def select_geography(self, value: str) -> "CreateAiModelPage":
        from selenium.webdriver.common.action_chains import ActionChains
        loc = (By.XPATH, AiModelsLocators.GEOGRAPHY_INPUT)
        el = self.wait_with_timeout(10).until(EC.presence_of_element_located(loc))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.driver.execute_script("arguments[0].click();", el)
        el.send_keys(value)
        time.sleep(1.5)
        el.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.3)
        el.send_keys(Keys.ENTER)
        time.sleep(0.3)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)
        return self

    def _scroll_and_select(self, locator, value: str):
        from selenium.webdriver.common.action_chains import ActionChains

        el = self.wait_with_timeout(10).until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)

        # JS click to bypass any toast/overlay that would intercept a real click
        self.driver.execute_script("arguments[0].click();", el)
        el.clear()
        el.send_keys(value)

        xpath = f"//div[@role='option' and normalize-space(.)='{value}']"
        opt = self.wait_with_timeout(10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            opt.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", opt)

        time.sleep(0.5)
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_for_autosave(trigger_blur=False)
        time.sleep(1.5)

    # ── Version tab ───────────────────────────────────────────────────────────

    def create_version(self, version_name: str = "1.0") -> "CreateAiModelPage":
        """Open the new-version dialog, optionally set name, then save."""
        try:
            # First run: "Create First Version" placeholder button
            btn = self.wait_with_timeout(5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, AiModelsLocators.CREATE_FIRST_VERSION_BTN)
                )
            )
        except TimeoutException:
            # Subsequent runs: "NEW VERSION" button
            btn = self.wait_with_timeout(10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, AiModelsLocators.NEW_VERSION_BTN)
                )
            )
        self.driver.execute_script("arguments[0].click();", btn)

        # Dialog should open
        name_input = self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.VERSION_NAME_INPUT))
        )
        name_input.clear()
        name_input.send_keys(Keys.CONTROL + "a")
        name_input.send_keys(Keys.DELETE)
        name_input.send_keys(version_name)

        save_btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, AiModelsLocators.SAVE_VERSION_BTN))
        )
        self.driver.execute_script("arguments[0].click();", save_btn)

        # Wait for dialog to close
        self.wait_with_timeout(10).until(
            EC.invisibility_of_element_located((By.XPATH, AiModelsLocators.SAVE_VERSION_BTN))
        )
        return self

    def add_access_method(self, endpoint_url: str) -> "CreateAiModelPage":
        """Click '+ Add Access Method', fill endpoint URL, then save."""
        btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, AiModelsLocators.ADD_ACCESS_METHOD_BTN))
        )
        self.driver.execute_script("arguments[0].click();", btn)

        # Fill the required API endpoint URL field
        url_input = self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.API_ENDPOINT_INPUT))
        )
        url_input.clear()
        url_input.send_keys(endpoint_url)

        add_btn = self.wait_with_timeout(10).until(
            EC.element_to_be_clickable((By.XPATH, AiModelsLocators.ADD_PROVIDER_BTN))
        )
        self.driver.execute_script("arguments[0].click();", add_btn)

        # Wait for dialog to close
        self.wait_with_timeout(10).until(
            EC.invisibility_of_element_located((By.XPATH, AiModelsLocators.ADD_PROVIDER_BTN))
        )
        return self

    # ── Publish tab ───────────────────────────────────────────────────────────

    def is_publish_button_enabled(self) -> bool:
        # The opub-ui Publish button has no HTML disabled attr even when fields are missing;
        # React shows a validation error instead. True "enabled" means no missing-field error.
        try:
            self.wait_with_timeout(20).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, AiModelsLocators.METADATA_MISSING_ERROR)
                )
            )
            return True
        except TimeoutException:
            return False

    def click_publish(self) -> "CreateAiModelPage":
        # Wait for validation errors to clear before clicking
        try:
            self.wait_with_timeout(20).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, AiModelsLocators.METADATA_MISSING_ERROR)
                )
            )
        except TimeoutException:
            pass  # Proceed; is_published() will catch the failure
        btn = self.wait_with_timeout(15).until(
            EC.element_to_be_clickable((By.XPATH, AiModelsLocators.PUBLISH_BTN))
        )
        self.driver.execute_script("arguments[0].click();", btn)
        return self

    def is_published(self) -> bool:
        """After clicking Publish, wait for the model-is-published status text."""
        try:
            self.wait_with_timeout(20).until(
                lambda d: "?tab=published" in d.current_url
                or d.find_elements(By.XPATH, AiModelsLocators.MODEL_PUBLISHED_TXT)
            )
            return True
        except TimeoutException:
            return False

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_description_text(self) -> str:
        el = self.wait_with_timeout(10).until(
            EC.visibility_of_element_located((By.XPATH, AiModelsLocators.DESCRIPTION_EDITOR))
        )
        return el.text.strip()
