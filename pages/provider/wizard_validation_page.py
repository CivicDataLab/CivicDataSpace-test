# pages/provider/wizard_validation_page.py

from selenium.common.exceptions import TimeoutException

from locators.provider.editor_wizard_locators import EditorWizardLocators as W
from pages.provider.editor_wizard_page import EditorWizardPage

# The box of the visible element whose own text starts with arguments[0], in viewport coordinates.
_BOX_JS = """
var text = arguments[0], found = null;
document.querySelectorAll('main *').forEach(function (e) {
  var own = Array.from(e.childNodes).filter(function (n) { return n.nodeType == 3; })
    .map(function (n) { return n.textContent; }).join('').trim();
  if (own.indexOf(text) === 0 && e.offsetParent !== null) { found = e; }
});
if (!found) return null;
var b = found.getBoundingClientRect();
return {top: b.top, bottom: b.bottom, viewport: window.innerHeight};
"""

# Messages of visible field errors (elements whose id ends in -error) that no
# aria-invalid control points to through aria-describedby.
_UNASSOCIATED_JS = """
var out = [];
document.querySelectorAll('main [id$="-error"]').forEach(function (err) {
  if (err.offsetParent === null || !err.textContent.trim()) return;
  var linked = false;
  document.querySelectorAll('[aria-describedby]').forEach(function (c) {
    if ((c.getAttribute('aria-describedby') || '').split(/\\s+/).indexOf(err.id) >= 0 &&
        c.getAttribute('aria-invalid') === 'true') linked = true;
  });
  if (!linked) out.push(err.textContent.trim());
});
return out;
"""


class WizardValidationPage(EditorWizardPage):
    """What a wizard step says when Continue is pressed with required fields missing."""

    def message_box(self, text: str):
        """Where the visible message starting with `text` sits, or None when it is not shown."""
        return self.driver.execute_script(_BOX_JS, text)

    def press_continue(self, first_message: str) -> "WizardValidationPage":
        """Press Continue once the step has missing fields and wait for `first_message` to show.

        Fails if the editor moves on instead, or if the message never appears.
        """
        before = self.driver.current_url
        try:
            self.click_until(
                W.CONTINUE_BUTTON, lambda d: self.message_box(first_message) is not None,
                attempts=1, wait_each=15,
                message=f"No {first_message!r} message after pressing Continue",
            )
        except TimeoutException as exc:
            moved = " (the editor moved on)" if self.driver.current_url != before else ""
            raise AssertionError(f"{exc.msg}{moved}") from None
        assert self.driver.current_url == before, "Continue moved on although required fields are missing"
        return self

    def has_message(self, text: str) -> bool:
        return self.message_box(text) is not None

    def is_in_view(self, text: str) -> bool:
        """Is the message `text` fully inside the visible part of the window?"""
        box = self.message_box(text)
        return bool(box) and box["top"] >= 0 and box["bottom"] <= box["viewport"]

    def unassociated_errors(self) -> list[str]:
        """Visible field errors that no invalid control is linked to."""
        return self.driver.execute_script(_UNASSOCIATED_JS)
