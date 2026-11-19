# locators/accessibility_locators.py
"""
Locators for the "Accessibility Options" widget.

NOTE: as of 2026-08-24 this widget is not present on either
dev.civicdataspace.in or civicdataspace.in. These locators describe the agreed
target design, and the tests in tests/accessibility/test_a11y_006_widget.py act
as its acceptance criteria — they report NOT IMPLEMENTED until it ships.

Each control is matched by its visible label plus common alternatives, so the
tests keep working whether the implementation renders <button>, <a role=button>
or an <input> toggle.
"""

from selenium.webdriver.common.by import By


def _control(*labels: str) -> tuple:
    """Match a widget control by any of its accepted visible/accessible names."""
    conditions = []
    for label in labels:
        norm = label.lower().replace(" ", "")
        conditions.append(
            "translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ ', 'abcdefghijklmnopqrstuvwxyz')"
            f"={norm!r}"
        )
        conditions.append(
            "translate(normalize-space(@aria-label), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ ', 'abcdefghijklmnopqrstuvwxyz')"
            f"={norm!r}"
        )
    predicate = " or ".join(conditions)
    return (
        By.XPATH,
        f"//*[self::button or self::a or self::input or @role='button'][{predicate}]",
    )


class AccessibilityWidgetLocators:
    # Widget container / launcher
    PANEL = (
        By.XPATH,
        "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        " 'abcdefghijklmnopqrstuvwxyz'), 'accessibility options')]",
    )
    LAUNCHER = (
        By.XPATH,
        "//*[self::button or self::a or @role='button']"
        "[contains(translate(normalize-space(@aria-label),"
        " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accessibility')]",
    )

    # Text sizing
    LARGE_TEXT = _control("Large Text", "Increase Text", "Bigger Text")
    SMALL_TEXT = _control("Small Text", "Decrease Text", "Smaller Text")
    RESET_TEXT = _control("Reset Text")

    # Visual presentation
    LIGHT_DARK = _control("Light/Dark", "Light Dark", "Toggle Theme", "Dark Mode")
    GRAYSCALE = _control("Grayscale", "Greyscale")
    HIGH_CONTRAST = _control("High Contrast")
    DYSLEXIA = _control("Dyslexia", "Dyslexia Friendly", "Dyslexic Font")

    # Speech
    READ_ALOUD = _control("Read Aloud")
    SPEAK = _control("Speak")
    SPEED_UP = _control("Speed Up")
    SPEED_DOWN = _control("Speed Down")
    RESET_SPEED = _control("Reset Speed")
    WHOLE_PAGE = _control("Whole Page")


# Control inventory used to drive the parametrised widget tests.
# (id, locator attribute name, human label, what it must demonstrably change)
WIDGET_CONTROLS = [
    ("large-text",    "LARGE_TEXT",    "Large Text",    "root font size increases"),
    ("small-text",    "SMALL_TEXT",    "Small Text",    "root font size decreases"),
    ("reset-text",    "RESET_TEXT",    "Reset Text",    "root font size returns to default"),
    ("light-dark",    "LIGHT_DARK",    "Light/Dark",    "background/foreground colours invert"),
    ("grayscale",     "GRAYSCALE",     "Grayscale",     "a grayscale filter is applied"),
    ("high-contrast", "HIGH_CONTRAST", "High Contrast", "contrast ratio increases"),
    ("dyslexia",      "DYSLEXIA",      "Dyslexia",      "a dyslexia-friendly font is applied"),
    ("read-aloud",    "READ_ALOUD",    "Read Aloud",    "speech synthesis starts"),
    ("speak",         "SPEAK",         "Speak",         "speech synthesis starts"),
    ("speed-up",      "SPEED_UP",      "Speed Up",      "speech rate increases"),
    ("speed-down",    "SPEED_DOWN",    "Speed Down",    "speech rate decreases"),
    ("reset-speed",   "RESET_SPEED",   "Reset Speed",   "speech rate returns to default"),
    ("whole-page",    "WHOLE_PAGE",    "Whole Page",    "read-aloud scope covers the page"),
]
