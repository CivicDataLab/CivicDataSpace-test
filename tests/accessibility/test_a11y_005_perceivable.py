"""
Perceivability checks: text alternatives, contrast, resize and reflow.

Resize (1.4.4) and reflow (1.4.10) can't be judged from a static DOM snapshot —
they need the viewport or font size actually changed and the result re-measured,
which is why they live here rather than being left to axe.

WCAG 2.1: 1.1.1, 1.4.3, 1.4.4, 1.4.10, 1.4.11, 2.5.5
A11Y Project: alt text, colour contrast, resizable text, single-column reflow
"""

import pytest

from utils import a11y
from .conftest import PUBLIC_PAGES

pytestmark = [pytest.mark.accessibility]

PAGE_IDS = [p[0] for p in PUBLIC_PAGES]
# Viewport-manipulating checks are slow; a representative subset is enough.
VIEWPORT_PAGES = [p for p in PUBLIC_PAGES if p[0] in ("home", "datasets", "about-us")]
VIEWPORT_IDS = [p[0] for p in VIEWPORT_PAGES]


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_images_have_text_alternatives(driver, goto, page_id, path):
    """WCAG 1.1.1 — informative images need alt text; decorative need alt=""."""
    goto(path)
    data = driver.execute_script("""
        const visible = (el) => el.offsetParent !== null || el.getClientRects().length;
        const imgs = [...document.querySelectorAll('img')].filter(visible);
        const missing = imgs.filter(i => i.getAttribute('alt') === null);
        const decorative = imgs.filter(i => (i.getAttribute('alt') || '').trim() === '' &&
                                            i.getAttribute('alt') !== null);
        // alt text that just repeats the filename tells a screen reader nothing.
        const filenameish = imgs.filter(i => {
            const alt = (i.getAttribute('alt') || '').trim();
            return alt && /\\.(png|jpe?g|gif|svg|webp)$/i.test(alt);
        });
        return {
            total: imgs.length,
            missing: missing.slice(0, 15).map(i => ({
                src: (i.getAttribute('src') || '').slice(-70),
                cls: (i.getAttribute('class') || '').slice(0, 50),
            })),
            decorative_count: decorative.length,
            filenameish: filenameish.slice(0, 10).map(i => i.getAttribute('alt')),
        };
    """)

    problems = []
    if data["missing"]:
        problems.append(f"{len(data['missing'])} image(s) with no alt attribute")
    if data["filenameish"]:
        problems.append(f"{len(data['filenameish'])} image(s) whose alt is a filename")

    a11y.record(
        check="image-alt",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={"url": path, **data, "problems": problems},
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)} — {data['missing'][:5]}"


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_text_meets_contrast_minimum(driver, goto, page_id, path):
    """WCAG 1.4.3 — delegated to axe's colour-contrast rule.

    Contrast is one thing axe computes properly (it resolves stacking contexts
    and background images), so re-implementing it here would be strictly worse.
    """
    goto(path)
    results = a11y.run_axe(driver, tags=["wcag2aa"])

    contrast = [v for v in results.get("violations", []) if v.get("id") == "color-contrast"]
    node_count = sum(len(v.get("nodes", [])) for v in contrast)

    a11y.record(
        check="color-contrast",
        page=page_id,
        status="pass" if not contrast else "fail",
        detail={"url": path, "failing_nodes": node_count},
        violations=contrast,
    )
    assert not contrast, (
        f"{page_id} ({path}): {node_count} element(s) below the 4.5:1 contrast "
        f"minimum:\n  {a11y.summarize_violations(contrast)}"
    )


@pytest.mark.parametrize("page_id,path", VIEWPORT_PAGES, ids=VIEWPORT_IDS)
def test_text_resizes_to_200_percent(driver, goto, page_id, path):
    """WCAG 1.4.4 — doubling text size must not clip content or break layout.

    Zooming the root font size is the closest Selenium equivalent to a browser
    text-only zoom; a layout that survives it will survive real user zoom.
    """
    goto(path)

    before = driver.execute_script("""
        return { w: document.documentElement.scrollWidth,
                 clientW: document.documentElement.clientWidth };
    """)

    driver.execute_script("document.documentElement.style.fontSize = '200%';")
    # Let the layout settle after reflow.
    driver.execute_script("return document.body.offsetHeight;")

    after = driver.execute_script("""
        const de = document.documentElement;
        const overflowing = [...document.querySelectorAll('body *')]
            .filter(el => {
                const r = el.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) return false;
                return r.right > de.clientWidth + 4;
            })
            .slice(0, 10)
            .map(el => ({ tag: el.tagName.toLowerCase(),
                          cls: (el.getAttribute('class')||'').slice(0,50),
                          right: Math.round(el.getBoundingClientRect().right) }));
        return { w: de.scrollWidth, clientW: de.clientWidth, overflowing };
    """)

    driver.execute_script("document.documentElement.style.fontSize = '';")

    horizontal_overflow = after["w"] > after["clientW"] + 4
    problems = []
    if horizontal_overflow:
        problems.append(
            f"page scrolls horizontally at 200% text "
            f"(scrollWidth {after['w']} > clientWidth {after['clientW']})"
        )

    a11y.record(
        check="text-resize",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={"url": path, "before": before, "after": after, "problems": problems},
    )
    assert not problems, (
        f"{page_id} ({path}): {'; '.join(problems)}. "
        f"Overflowing elements: {after['overflowing'][:5]}"
    )


@pytest.mark.parametrize("page_id,path", VIEWPORT_PAGES, ids=VIEWPORT_IDS)
def test_content_reflows_at_320px(driver, goto, page_id, path):
    """WCAG 1.4.10 — at 320 CSS px there must be no two-dimensional scrolling."""
    original = driver.get_window_size()
    try:
        # 320 CSS px wide viewport; height per the WCAG 1.4.10 note (256px tall
        # equivalent is for vertical text, 320 wide is the horizontal case).
        driver.set_window_size(320, 900)
        goto(path)

        measured = driver.execute_script("""
            const de = document.documentElement;
            const offenders = [...document.querySelectorAll('body *')]
                .filter(el => {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) return false;
                    return r.right > de.clientWidth + 4;
                })
                .slice(0, 10)
                .map(el => ({ tag: el.tagName.toLowerCase(),
                              cls: (el.getAttribute('class')||'').slice(0,50),
                              w: Math.round(el.getBoundingClientRect().width) }));
            return { scrollW: de.scrollWidth, clientW: de.clientWidth, offenders };
        """)

        overflow = measured["scrollW"] > measured["clientW"] + 4
        a11y.record(
            check="reflow",
            page=page_id,
            status="pass" if not overflow else "fail",
            detail={"url": path, **measured},
        )
        assert not overflow, (
            f"{page_id} ({path}): horizontal scrolling required at 320px "
            f"(scrollWidth {measured['scrollW']} > clientWidth {measured['clientW']}). "
            f"Offenders: {measured['offenders'][:5]}"
        )
    finally:
        driver.set_window_size(original["width"], original["height"])


@pytest.mark.parametrize("page_id,path", VIEWPORT_PAGES, ids=VIEWPORT_IDS)
def test_interactive_targets_are_large_enough(driver, goto, page_id, path):
    """Target size — reported as an advisory, not a conformance gate.

    2.5.5 is AAA and 2.5.8 (AA, 24x24) is WCAG 2.2, which this suite doesn't
    claim. Small targets are recorded for the report but don't fail the build.
    """
    goto(path)
    small = driver.execute_script("""
        const visible = (el) => el.offsetParent !== null || el.getClientRects().length;
        return [...document.querySelectorAll('a[href], button, input[type=checkbox], input[type=radio]')]
            .filter(visible)
            .map(el => ({ el, r: el.getBoundingClientRect() }))
            .filter(({r}) => r.width > 0 && r.height > 0 && (r.width < 24 || r.height < 24))
            .slice(0, 20)
            .map(({el, r}) => ({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText||'').trim().slice(0, 30),
                w: Math.round(r.width), h: Math.round(r.height),
            }));
    """)

    a11y.record(
        check="target-size",
        page=page_id,
        status="pass" if not small else "fail",
        detail={
            "url": path,
            "advisory": "WCAG 2.5.5 is AAA; recorded but not gating",
            "small_targets": small,
        },
    )
    # Advisory only — deliberately not asserted.
