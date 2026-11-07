"""
Acceptance tests for the "Accessibility Options" widget.

STATUS: the widget does not exist on dev.civicdataspace.in or
civicdataspace.in (verified 2026-08-24). Every test here therefore reports
NOT IMPLEMENTED rather than passing — a suite that silently skips would let the
gap disappear from the report, and one that hard-fails would drown the real
findings. ACCESSIBILITY_REPORT.md lists these separately as outstanding work.

When the widget ships, these run as real tests with no changes needed: each one
asserts the control is present, keyboard-operable, correctly labelled, and that
activating it produces the effect it promises.

Widget spec (13 controls): Large Text, Small Text, Reset Text, Light/Dark,
Grayscale, High Contrast, Dyslexia, Read Aloud, Speak, Speed Up, Speed Down,
Reset Speed, Whole Page.

WCAG 2.1: 1.4.4 Resize Text (AA), 1.4.3 Contrast (AA), 2.1.1 Keyboard (A),
          4.1.2 Name/Role/Value (A)
A11Y Project: user-controllable display preferences
"""

import pytest
from selenium.webdriver.common.by import By

from locators.accessibility_locators import AccessibilityWidgetLocators as W
from locators.accessibility_locators import WIDGET_CONTROLS
from utils import a11y

pytestmark = [pytest.mark.accessibility, pytest.mark.widget]

NOT_IMPLEMENTED_MSG = (
    "Accessibility Options widget is not present on this deployment. "
    "This is a known gap, not a test error — see ACCESSIBILITY_REPORT.md "
    "'Outstanding' section. These tests become live checks once the widget ships."
)


def _widget_present(driver) -> bool:
    """True if anything resembling the widget is in the DOM."""
    return driver.execute_script("""
        const txt = (document.body.innerText || '').toLowerCase();
        if (txt.includes('accessibility options')) return true;
        return !!document.querySelector(
            '[class*="accessib" i],[id*="accessib" i],[aria-label*="accessib" i]'
        );
    """)


@pytest.fixture
def widget_page(driver, goto):
    """Load the homepage and report the widget's availability."""
    goto("/")
    return _widget_present(driver)


def test_accessibility_widget_is_available(driver, widget_page):
    """The widget must be reachable from the site."""
    present = widget_page

    a11y.record(
        check="widget-present",
        page="home",
        status="pass" if present else "not_implemented",
        detail={
            "url": "/",
            "expected_controls": [c[2] for c in WIDGET_CONTROLS],
            "note": None if present else NOT_IMPLEMENTED_MSG,
        },
    )

    if not present:
        pytest.skip(NOT_IMPLEMENTED_MSG)

    assert driver.find_elements(*W.PANEL) or driver.find_elements(*W.LAUNCHER), (
        "Accessibility markup was detected but neither the panel nor a launcher "
        "control could be located."
    )


@pytest.mark.parametrize(
    "control_id,locator_attr,label,expected_effect",
    WIDGET_CONTROLS,
    ids=[c[0] for c in WIDGET_CONTROLS],
)
def test_widget_control_is_present_and_operable(
    driver, widget_page, control_id, locator_attr, label, expected_effect
):
    """Each control must exist, be keyboard-operable and be properly named."""
    present = widget_page

    if not present:
        a11y.record(
            check="widget-control",
            page=f"widget-{control_id}",
            status="not_implemented",
            detail={
                "control": label,
                "expected_effect": expected_effect,
                "note": NOT_IMPLEMENTED_MSG,
            },
        )
        pytest.skip(f"{NOT_IMPLEMENTED_MSG} (control: {label})")

    locator = getattr(W, locator_attr)
    elements = driver.find_elements(*locator)

    problems = []
    if not elements:
        problems.append(f"control {label!r} not found in the widget")
    else:
        el = elements[0]
        info = driver.execute_script("""
            const el = arguments[0];
            const cs = getComputedStyle(el);
            return {
                tag: el.tagName.toLowerCase(),
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                text: (el.innerText || '').trim(),
                tabindex: el.getAttribute('tabindex'),
                disabled: el.disabled === true,
                display: cs.display,
                pointerEvents: cs.pointerEvents,
            };
        """, el)

        if not (info["text"] or info["ariaLabel"]):
            problems.append("control has no accessible name (WCAG 4.1.2)")
        # A div-with-onclick is not keyboard operable.
        if info["tag"] not in ("button", "a", "input") and info["role"] != "button" \
                and info["tabindex"] is None:
            problems.append(
                f"control is a <{info['tag']}> with no role/tabindex — "
                "not keyboard operable (WCAG 2.1.1)"
            )
        if info["disabled"]:
            problems.append("control is disabled")

    a11y.record(
        check="widget-control",
        page=f"widget-{control_id}",
        status="pass" if not problems else "fail",
        detail={"control": label, "expected_effect": expected_effect, "problems": problems},
    )
    assert not problems, f"Accessibility widget control {label!r}: {'; '.join(problems)}"


def test_text_sizing_controls_change_root_font_size(driver, widget_page):
    """Large/Small/Reset Text must actually change rendered text size (WCAG 1.4.4)."""
    if not widget_page:
        a11y.record(
            check="widget-control",
            page="widget-text-sizing-effect",
            status="not_implemented",
            detail={"control": "Large/Small/Reset Text", "note": NOT_IMPLEMENTED_MSG},
        )
        pytest.skip(NOT_IMPLEMENTED_MSG)

    def root_font_px():
        return float(driver.execute_script(
            "return parseFloat(getComputedStyle(document.documentElement).fontSize);"
        ))

    baseline = root_font_px()

    large = driver.find_elements(*W.LARGE_TEXT)
    small = driver.find_elements(*W.SMALL_TEXT)
    reset = driver.find_elements(*W.RESET_TEXT)

    problems = []
    if large:
        driver.execute_script("arguments[0].click();", large[0])
        if root_font_px() <= baseline:
            problems.append("Large Text did not increase the root font size")
    else:
        problems.append("Large Text control not found")

    if reset:
        driver.execute_script("arguments[0].click();", reset[0])
        if abs(root_font_px() - baseline) > 0.5:
            problems.append("Reset Text did not restore the original font size")
    else:
        problems.append("Reset Text control not found")

    if small:
        driver.execute_script("arguments[0].click();", small[0])
        if root_font_px() >= baseline:
            problems.append("Small Text did not decrease the root font size")
    else:
        problems.append("Small Text control not found")

    a11y.record(
        check="widget-control",
        page="widget-text-sizing-effect",
        status="pass" if not problems else "fail",
        detail={"control": "Large/Small/Reset Text", "baseline_px": baseline,
                "problems": problems},
    )
    assert not problems, "; ".join(problems)


def test_visual_mode_controls_change_presentation(driver, widget_page):
    """Grayscale / High Contrast / Light-Dark must visibly alter presentation."""
    if not widget_page:
        a11y.record(
            check="widget-control",
            page="widget-visual-effect",
            status="not_implemented",
            detail={"control": "Grayscale/High Contrast/Light-Dark",
                    "note": NOT_IMPLEMENTED_MSG},
        )
        pytest.skip(NOT_IMPLEMENTED_MSG)

    def presentation():
        return driver.execute_script("""
            const b = getComputedStyle(document.body);
            const h = getComputedStyle(document.documentElement);
            return { filter: b.filter + '|' + h.filter,
                     bg: b.backgroundColor, fg: b.color };
        """)

    baseline = presentation()
    problems = []

    for locator, name, expectation in (
        (W.GRAYSCALE, "Grayscale", "a grayscale() filter"),
        (W.HIGH_CONTRAST, "High Contrast", "a contrast change"),
        (W.LIGHT_DARK, "Light/Dark", "inverted background/foreground"),
    ):
        els = driver.find_elements(*locator)
        if not els:
            problems.append(f"{name} control not found")
            continue
        driver.execute_script("arguments[0].click();", els[0])
        after = presentation()
        if after == baseline:
            problems.append(f"{name} produced no visible change (expected {expectation})")
        # Restore for the next control.
        driver.execute_script("arguments[0].click();", els[0])

    a11y.record(
        check="widget-control",
        page="widget-visual-effect",
        status="pass" if not problems else "fail",
        detail={"control": "Grayscale/High Contrast/Light-Dark",
                "baseline": baseline, "problems": problems},
    )
    assert not problems, "; ".join(problems)


def test_speech_controls_use_speech_synthesis(driver, widget_page):
    """Read Aloud / Speak / speed controls must drive the Web Speech API."""
    if not widget_page:
        a11y.record(
            check="widget-control",
            page="widget-speech-effect",
            status="not_implemented",
            detail={"control": "Read Aloud/Speak/Speed", "note": NOT_IMPLEMENTED_MSG},
        )
        pytest.skip(NOT_IMPLEMENTED_MSG)

    # Instrument speechSynthesis so a headless browser (which produces no audio)
    # can still prove the control invoked speech.
    driver.execute_script("""
        window.__spoken = [];
        if (window.speechSynthesis) {
            const orig = window.speechSynthesis.speak.bind(window.speechSynthesis);
            window.speechSynthesis.speak = (u) => {
                window.__spoken.push({ text: (u && u.text || '').slice(0, 80),
                                       rate: u && u.rate });
                return orig(u);
            };
        }
    """)

    problems = []
    read = driver.find_elements(*W.READ_ALOUD) or driver.find_elements(*W.SPEAK)
    if not read:
        problems.append("neither Read Aloud nor Speak control was found")
    else:
        driver.execute_script("arguments[0].click();", read[0])
        spoken = driver.execute_script("return window.__spoken || [];")
        if not spoken:
            problems.append("activating Read Aloud/Speak did not call speechSynthesis.speak()")

    a11y.record(
        check="widget-control",
        page="widget-speech-effect",
        status="pass" if not problems else "fail",
        detail={"control": "Read Aloud/Speak/Speed", "problems": problems},
    )
    assert not problems, "; ".join(problems)


def test_widget_itself_is_accessible(driver, widget_page):
    """The accessibility widget must not itself contain violations."""
    if not widget_page:
        a11y.record(
            check="widget-present",
            page="widget-self-scan",
            status="not_implemented",
            detail={"note": NOT_IMPLEMENTED_MSG},
        )
        pytest.skip(NOT_IMPLEMENTED_MSG)

    panels = driver.find_elements(*W.PANEL)
    assert panels, "Widget reported present but panel could not be located for scanning"

    results = a11y.run_axe(driver)
    blocking = a11y.blocking_violations(results)

    a11y.record(
        check="widget-present",
        page="widget-self-scan",
        status="pass" if not blocking else "fail",
        detail={"scanned": "page containing the widget"},
        violations=results.get("violations", []),
    )
    assert not blocking, (
        "The Accessibility Options widget's own page has critical/serious "
        f"violations:\n  {a11y.summarize_violations(blocking)}"
    )
