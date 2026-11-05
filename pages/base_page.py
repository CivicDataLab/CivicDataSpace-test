# pages/base_page.py
import os
import platform
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class BasePage:
    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait   = WebDriverWait(driver, timeout)

    def visit(self, url):
        self.driver.get(url)

    def find(self, by_locator):
        return self.wait.until(EC.visibility_of_element_located(by_locator))

    def finds(self, by_locator):
        return self.wait.until(EC.presence_of_all_elements_located(by_locator))

    def click(self, by_locator):
        elem = self.wait.until(EC.element_to_be_clickable(by_locator))
        elem.click()
        return elem

    # ── Text Input Utilities ──────────────────────────────────────────────────

    def clear_and_type(self, locator, text, timeout=10, retries=2, slow=False):
        """Robustly set input value; handles React/Angular controlled inputs."""
        for _ in range(retries + 1):
            el = self.wait.until(EC.element_to_be_clickable(locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()

            # 1) Triple-click + Ctrl/Cmd+A + Delete + native clear
            ActionChains(self.driver).double_click(el).perform()
            for mod in (Keys.CONTROL, Keys.COMMAND):
                try:
                    el.send_keys(mod, "a")
                except Exception:
                    pass
            el.send_keys(Keys.DELETE)
            try:
                el.clear()
            except Exception:
                pass

            # 2) If still has text, backspace its length
            val = (el.get_attribute("value") or "")
            if val:
                el.send_keys(Keys.END)
                for _ in range(len(val)):
                    el.send_keys(Keys.BACKSPACE)

            # 3) If STILL not empty, use React-safe native setter + events
            if (el.get_attribute("value") or "").strip():
                self.driver.execute_script("""
                    const e = arguments[0];
                    const desc = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
                    if (desc && desc.set) desc.set.call(e, '');
                    else e.value = '';
                    e.dispatchEvent(new Event('input', {bubbles:true}));
                    e.dispatchEvent(new Event('change', {bubbles:true}));
                """, el)

            # Type and verify
            if slow:
                for ch in text:
                    el.send_keys(ch)
            else:
                el.send_keys(text)

            self.driver.execute_script("arguments[0].blur();", el)
            if (el.get_attribute("value") or "").strip() == text:
                return el

        raise AssertionError(f"Could not set value to '{text}'.")

    def type_text(self, locator, text):
        """Type text without clearing"""
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.send_keys(text)
        return element

    def clear_field(self, locator):
        """Clear input field"""
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.clear()
        return element

    # ── Dropdown & Selection Utilities ────────────────────────────────────────

    def select_dropdown_by_text(self, locator, text):
        """Select from native <select> dropdown by visible text"""
        from selenium.webdriver.support.ui import Select
        element = self.wait.until(EC.presence_of_element_located(locator))
        Select(element).select_by_visible_text(text)
        return element

    def wait_until_saved(self, timeout=30):
        """Wait until no autosave is in flight.

        Editor forms save on every field change. A dropdown opened while a save is
        running gets re-rendered away and the choice is lost: test_prv_007's retry
        screenshot shows SDG Goals empty with 'Saving...' still spinning. Returns
        at once when nothing is saving.
        """
        from selenium.webdriver.common.by import By

        self.wait_with_timeout(timeout).until(
            EC.invisibility_of_element_located((By.XPATH, "//*[normalize-space(text())='Saving...']")),
            message="Timed out waiting for the editor autosave to finish",
        )

    def get_combobox_options(self, input_locator) -> list[str]:
        """Open a combobox and return the label of every option it lists."""
        from selenium.webdriver.common.by import By

        self.wait_until_saved()
        combo = self.wait.until(EC.presence_of_element_located(input_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", combo)
        # A JS click: these lists don't close on Escape, Tab or blur, so a list
        # opened earlier can sit over this input and swallow a real click.
        self.driver.execute_script("arguments[0].click();", combo)
        # Other comboboxes' options stay in the DOM, so read only this one's
        # listbox, which the input names in aria-controls.
        listbox = combo.get_attribute("aria-controls")
        assert listbox, "Combobox input has no aria-controls listbox"
        options = self.wait_with_timeout(30).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//*[@id='{listbox}']//*[@role='option']")),
            message="Combobox opened but listed no options",
        )
        # textContent, not .text: options scrolled out of the list's viewport
        # count as not displayed and would come back empty.
        return [o.get_attribute("textContent").strip() for o in options]

    def wait_for_option(self, combo, option_text, timeout=30):
        """Wait for a clickable role=option with exactly this text.

        On timeout, name the options this combobox DID list. A blank
        TimeoutException here made a missing sector ("Budgets", dropped by the
        dev refresh) read as flakiness across five tests and every rerun.
        """
        xpath = f"//div[@role='option' and normalize-space(.)='{option_text}']"
        try:
            return self.wait_with_timeout(timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except TimeoutException:
            # Other widgets (e.g. the Bhashini language list) keep role=option
            # nodes in the DOM, so read only this input's listbox.
            listbox = combo.get_attribute("aria-controls")
            scope = f"//*[@id='{listbox}']" if listbox else ""
            listed = [o.get_attribute("textContent").strip()
                      for o in self.driver.find_elements(By.XPATH, f"{scope}//*[@role='option']")]
            raise TimeoutException(
                f"No option {option_text!r} after {timeout}s. Options listed (filtered by the typed text): {listed}"
            ) from None

    def select_combobox_option(self, input_locator, option_text):
        """
        Generic combobox selection - click input, type, select option, close dropdown.
        Works with React/custom dropdowns that aren't native <select> elements.
        """
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import ElementClickInterceptedException

        self.wait_until_saved()
        combo = self.wait.until(EC.element_to_be_clickable(input_locator))
        combo.click()
        combo.clear()
        combo.send_keys(option_text)

        # Options are often populated by a GraphQL query on page load, so allow
        # the same 30s select_sdg_goals already uses for its option list.
        opt = self.wait_for_option(combo, option_text, timeout=30)

        try:
            opt.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", opt)

        import time
        time.sleep(0.5)

        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return self

    def set_react_select_by_text(self, locator, text):
        """Select a native <select> option by visible text the React-safe way.

        Select.select_by_visible_text updates the DOM but bypasses React's tracked setter, so
        the debounced (blur-driven) autosave never persists it. Set the value via the native
        setter + change event, then dispatch a bubbling focusout to trigger the blur autosave.
        """
        # The native <select> is visually hidden behind a custom-styled component, so it is
        # not "clickable" and cannot be real-clicked. Use presence and drive it via JS,
        # dispatching a bubbling focusout (React's onBlur listens at the root, so the event
        # need not come from a truly focused element) to trigger the blur autosave.
        el = self.wait.until(EC.presence_of_element_located(locator))
        matched = self.driver.execute_script(
            """
            const sel = arguments[0], text = arguments[1];
            const opt = Array.from(sel.options).find(
                o => o.textContent.trim() === text);
            if (!opt) return false;
            const setter = Object.getOwnPropertyDescriptor(
                HTMLSelectElement.prototype, 'value').set;
            setter.call(sel, opt.value);
            sel.dispatchEvent(new Event('input', {bubbles: true}));
            sel.dispatchEvent(new Event('change', {bubbles: true}));
            sel.dispatchEvent(new Event('blur', {bubbles: false}));
            sel.dispatchEvent(new Event('focusout', {bubbles: true}));
            return true;
            """,
            el, text
        )
        if not matched:
            raise AssertionError(f"No <select> option with text '{text}'")
        return el

    # ── Wait Utilities ─────────────────────────────────────────────────────────

    def wait_for_invisibility(self, locator, timeout=None):
        """Wait for element to become invisible"""
        wait = WebDriverWait(self.driver, timeout) if timeout else self.wait
        return wait.until(EC.invisibility_of_element_located(locator))

    def wait_for_url_contains(self, text, timeout=10):
        """Wait for URL to contain specific text"""
        return WebDriverWait(self.driver, timeout).until(
            lambda d: text in d.current_url
        )

    def wait_with_timeout(self, timeout):
        """Create a one-off wait with custom timeout"""
        return WebDriverWait(self.driver, timeout)

    def list_view_state(self, locators, timeout: int = 30) -> str:
        """Which end state a drafts/published list page settled into.

        `locators` needs EMPTY_DRAFTS_MESSAGE, EMPTY_PUBLISHED_MESSAGE and LIST_ROWS.
        Returns 'drafts_empty', 'published_empty' or 'rows'.
        """
        states = {
            "drafts_empty": locators.EMPTY_DRAFTS_MESSAGE,
            "published_empty": locators.EMPTY_PUBLISHED_MESSAGE,
            "rows": locators.LIST_ROWS,
        }

        def settled(d):
            for name, loc in states.items():
                if any(el.is_displayed() for el in d.find_elements(*loc)):
                    return name
            return False

        return self.wait_with_timeout(timeout).until(
            settled, message=f"List page never showed rows or an empty state: {self.driver.current_url}"
        )

    def save_failure_artifacts(self, tag: str) -> None:
        """Dump a screenshot + DOM so a timeout says what was actually on screen.

        Blank timeouts cost two wrong locator guesses on the publishers page and
        two useless timeout bumps here; the captured DOM is what settled both.
        """
        try:
            # Key the filename to the test and xdist worker. A fixed name means
            # each failure overwrites the previous one, and under -n the artifact
            # you read can belong to a different test than the one that failed --
            # which already sent one diagnosis down the wrong path.
            current = os.environ.get("PYTEST_CURRENT_TEST", "")
            test_id = current.split("::")[-1].split(" ")[0] or "unknown"
            worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
            stem = f"{tag}_{test_id}_{worker}_failure"
            self.driver.save_screenshot(f"{stem}.png")
            with open(f"{stem}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            # Console too. A screenshot shows a modal sitting open but not WHY:
            # a rejected GraphQL mutation leaves no visible toast, and without
            # this the DOM is a dead end.
            try:
                entries = self.driver.get_log("browser")
            except Exception:
                entries = []
            if entries:
                with open(f"{stem}.console.log", "w", encoding="utf-8") as f:
                    for e in entries:
                        f.write(f"{e.get('level')}: {e.get('message')}\n")
            # Network too: a clean console cannot distinguish "the click sent a
            # mutation that was rejected" from "the click sent nothing at all".
            try:
                perf = self.driver.get_log("performance")
            except Exception:
                perf = []
            if perf:
                import json as _json

                with open(f"{stem}.network.log", "w", encoding="utf-8") as f:
                    for e in perf:
                        msg = e.get("message", "")
                        if "graphql" not in msg.lower():
                            continue
                        try:
                            m = _json.loads(msg)["message"]
                        except Exception:
                            continue
                        method = m.get("method", "")
                        params = m.get("params", {})
                        if method == "Network.requestWillBeSent":
                            req = params.get("request", {})
                            f.write(f"SENT {req.get('method')} {req.get('url')}\n")
                            f.write(f"     body={str(req.get('postData'))[:400]}\n")
                        elif method == "Network.responseReceived":
                            f.write(f"RESP {params.get('response',{}).get('status')} "
                                    f"{params.get('response',{}).get('url')}\n")
        except Exception:
            pass

    def click_until(self, locator, condition, attempts=3, wait_each=20, message=""):
        """Click, then confirm it actually did something -- retry if it did not.

        A click on a Next.js page that has rendered but not yet hydrated hits a
        button that is visible and enabled and has no onClick attached yet. It
        raises nothing, logs nothing, and the app simply never responds:
        test_prv_006 sat on an open "Create New Dataset" modal for 60s with the
        type selected, the button aria-disabled=false, an empty console and no
        toast. `element_to_be_clickable` cannot see hydration, so the only
        reliable signal is whether the click had its expected effect.
        """
        last = None
        for attempt in range(attempts):
            el = self.wait.until(EC.element_to_be_clickable(locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            # First attempt native, later attempts JS. A native click can be
            # swallowed by an overlay at those coordinates WITHOUT Selenium
            # raising ElementClickIntercepted -- it reports success and the
            # handler never runs (test_prv_006: three clicks, and the network
            # log shows no mutation was ever sent). A dispatched JS click goes
            # straight to the element and still bubbles to React's listener.
            if attempt == 0:
                try:
                    el.click()
                except (ElementClickInterceptedException, StaleElementReferenceException) as exc:
                    last = exc
                    self.driver.execute_script("arguments[0].click();", el)
            else:
                self.driver.execute_script("arguments[0].click();", el)
            try:
                return self.wait_with_timeout(wait_each).until(condition)
            except TimeoutException as exc:
                last = exc
        raise TimeoutException(
            message or f"Click on {locator} never took effect after {attempts} attempts ({last})"
        )

    def type_into_rich_editor(self, locator, text: str) -> None:
        """Type into a Quill editor and make sure the text stays.

        Right after a record is created its editor can reset once, wiping what
        was typed (test_prv_012's CI screenshot: description empty). Type once,
        watch it for a few seconds, and type again if it was wiped -- more
        reliable than typing twice and asserting doubled text.
        """
        import time

        try:
            self.wait_for_invisibility((By.CLASS_NAME, "toast"), timeout=3)
        except TimeoutException:
            pass
        trace = []
        for attempt in (1, 2):
            self.wait_until_saved()
            fld = self.wait.until(
                EC.visibility_of_element_located(locator), message="Could not find the editor"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", fld)
            # Re-find immediately before typing: React can swap the editor node
            # between locating it and typing, and keys sent to the detached node
            # are accepted silently while the visible editor stays blank (the
            # captured screenshot showed the placeholder still in place).
            fld = self.driver.find_element(*locator)
            # Click, then focus. The click is what Quill needs: it tracks its own
            # selection range and sets it on mousedown/click, and without a caret
            # it silently discards everything send_keys types -- focus() alone
            # focuses the node but leaves Quill with no insertion point.
            # JS rather than a real click, which gets ElementClickIntercepted by
            # overlays (toast/tour) that are present but not yet gone.
            self.driver.execute_script(
                "arguments[0].click(); arguments[0].focus();", fld
            )
            active = self.driver.execute_script(
                "var a=document.activeElement;"
                "return a ? a.tagName+'.'+(a.className||'') : 'none';"
            )
            fld.send_keys(Keys.CONTROL + "a")
            fld.send_keys(Keys.DELETE)
            fld.send_keys(text)
            trace.append(
                f"attempt {attempt}: focused ok (activeElement={active}); "
                f"text right after send_keys={self.driver.find_element(*locator).text!r}"
            )
            # Wait for the text to land before watching whether it stays. Under
            # parallel load Quill can take a moment to commit, and polling
            # straight away burned both attempts in milliseconds.
            try:
                self.wait_with_timeout(10).until(
                    lambda d: d.find_element(*locator).text == text
                )
            except TimeoutException:
                trace.append(
                    f"attempt {attempt}: text never appeared within 10s; "
                    f"holds {self.driver.find_element(*locator).text!r}"
                )
                continue
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                if self.driver.find_element(*locator).text != text:
                    break
                time.sleep(0.5)
            else:
                return
        self.save_failure_artifacts("rich_editor")
        raise AssertionError(
            f"Editor kept losing typed text; now holds "
            f"{self.driver.find_element(*locator).text!r}\n" + "\n".join(trace)
        )

    def enter_date(self, locator, iso_date: str):
        """Set a <input type=date> to iso_date (YYYY-MM-DD) via the native JS setter.

        send_keys interprets keystrokes according to the OS locale (MM/DD/YYYY on Linux,
        DD/MM/YYYY on macOS), so the same keystroke string produces different dates on
        different platforms. Using the native setter bypasses locale entirely.

        The date field saves ONLY on blur, and its onBlur handler reads formData from the
        render closure: onBlur={() => handleSave(formData)}. If we blur immediately after
        dispatching change, React hasn't flushed the onChange state update yet, so the
        onBlur closure still holds the pre-change formData and persists startedOn: null —
        the input shows the date but the server never receives it. So we wait for React to
        re-render (input.value reflects the new date and a fresh onBlur closure is bound)
        BEFORE blurring, guaranteeing handleSave runs with the updated formData.
        """
        import time as _time
        self.wait_for_autosave()
        el = self.wait.until(EC.element_to_be_clickable(locator))
        # Focus first: the field saves only on blur, and blur() is a no-op unless the
        # element is the active element. Then set the value via the native setter and
        # dispatch input/change so React's onChange updates formData.startedOn.
        self.driver.execute_script(
            """
            const el = arguments[0], val = arguments[1];
            el.focus();
            const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            el, iso_date
        )
        # Wait for React to commit the onChange state update before blurring, so the
        # fresh onBlur closure captures the new date instead of stale formData.
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: el.get_attribute("value") == iso_date
            )
        except TimeoutException:
            pass
        _time.sleep(0.5)  # let React flush the re-render and rebind onBlur
        # Now fire a real blur (element is focused) plus a bubbling focusout so React's
        # onBlur runs handleSave with the updated formData and persists startedOn.
        self.driver.execute_script(
            """
            const el = arguments[0];
            el.blur();
            el.dispatchEvent(new Event('focusout', {bubbles: true}));
            """,
            el
        )
        self.wait_for_autosave(trigger_blur=False)
        return self

    # ── File Upload Utility ────────────────────────────────────────────────────

    def upload_file_to_dropzone(self, path_to_file, dropzone_class="DropZone-module_DropZone__xD9-6",
                                input_index=0):
        """
        Standard file upload to React DropZone component.
        Primary: send_keys after removing display:none (triggers real browser/React events + server upload).
        Fallback: JavaScript DataTransfer (updates client-side state only).

        input_index selects which file <input> to target when a form has several (e.g. the
        collaborative has separate logo (0) and cover image (1) dropzones); defaulting to the
        first preserves single-upload behaviour.
        """
        import os, time, base64
        from selenium.webdriver.common.by import By

        assert os.path.isfile(path_to_file), f"File does not exist: {path_to_file}"
        abs_path = os.path.abspath(path_to_file)
        file_name = os.path.basename(abs_path)
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}
        mime_type = mime_map.get(ext, "application/octet-stream")

        inputs = self.wait.until(
            lambda d: d.find_elements(By.XPATH, "//input[@type='file']") or False
        )
        if input_index >= len(inputs):
            raise AssertionError(
                f"Wanted file input #{input_index} but only {len(inputs)} present"
            )
        input_el = inputs[input_index]

        # Remove display:none so ChromeDriver can interact with the file input.
        # ChromeDriver uses CDP DOM.setFileInputFiles which triggers real browser events
        # (including React's synthetic onChange), enabling server-side upload.
        self.driver.execute_script("arguments[0].removeAttribute('style');", input_el)
        time.sleep(0.2)

        try:
            input_el.send_keys(abs_path)
            time.sleep(2)
            files_len = self.driver.execute_script("return arguments[0].files.length", input_el)
            if files_len > 0:
                return self
        except Exception:
            pass

        # Fallback: JavaScript DataTransfer (updates React state client-side)
        with open(abs_path, "rb") as f:
            file_b64 = base64.b64encode(f.read()).decode()

        self.driver.execute_script("""
            var b64 = arguments[0], name = arguments[1], mime = arguments[2], input = arguments[3];
            try {
                var bytes = atob(b64);
                var arr = new Uint8Array(bytes.length);
                for (var i = 0; i < bytes.length; i++) { arr[i] = bytes.charCodeAt(i); }
                var blob = new Blob([arr], {type: mime});
                var file = new File([blob], name, {type: mime});
                var dt = new DataTransfer();
                dt.items.add(file);
                Object.defineProperty(input, 'files', {writable: true, configurable: true, value: dt.files});
                var event = new Event('change', {bubbles: true, cancelable: false});
                input.dispatchEvent(event);
                return input.files.length;
            } catch(e) { return 'error: ' + e; }
        """, file_b64, file_name, mime_type, input_el)
        time.sleep(2)
        return self

    # ── Element State Utilities ────────────────────────────────────────────────

    def get_attribute(self, locator, attribute_name):
        """Get attribute value from element"""
        element = self.wait.until(EC.presence_of_element_located(locator))
        return element.get_attribute(attribute_name)

    def get_text(self, locator):
        """Get text content from element"""
        element = self.wait.until(EC.visibility_of_element_located(locator))
        return element.text.strip()

    def is_visible(self, locator, timeout=5):
        """
        Check if element is visible within timeout period.
        Returns True if visible, False if not found or not visible.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    # ── Advanced Interaction Utilities ─────────────────────────────────────────

    def scroll_to_element(self, locator):
        """Scroll element into view (center of viewport)"""
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
            element
        )
        return element

    def js_click(self, locator):
        """
        Click element via JavaScript (bypasses intercepted clicks).
        Use when standard click() fails due to overlays or animations.
        """
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].click();", element)
        return element

    # ── Autosave Utility ───────────────────────────────────────────────────────

    def wait_for_autosave(self, trigger_blur=True, timeout=15):
        """
        Wait for the editor autosave cycle to commit pending changes.

        Blurs the currently focused element via JavaScript to fire its onBlur
        handler (body.click() does not reliably blur inputs in Chrome), then
        waits for the 'Saving...' indicator to appear and resolve.
        Falls back to a generous sleep if the indicator is too fast to catch.
        """
        import time as _time
        from selenium.webdriver.common.by import By

        if trigger_blur:
            try:
                # JS blur reliably triggers React's onBlur; body.click() does not
                # move focus away from focusable elements in Chrome.
                self.driver.execute_script(
                    "var el = document.activeElement;"
                    "if (el && el.tagName !== 'BODY') { el.blur(); }"
                )
            except Exception:
                pass

        saving_locator = (By.XPATH, "//*[normalize-space(text())='Saving...']")

        try:
            # Poll at 100ms to catch brief Saving... indicator (default is 500ms)
            WebDriverWait(self.driver, 5, poll_frequency=0.1).until(
                EC.presence_of_element_located(saving_locator)
            )
            # Save in progress — wait until it finishes
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(saving_locator)
            )
            _time.sleep(0.3)
        except TimeoutException:
            # Saving... didn't appear — either already saved or save was too fast
            # to catch. Add a generous margin to ensure the network round-trip
            # completes before navigating away.
            _time.sleep(4)

        return self
