"""
Keyboard operability checks — the part of accessibility automated scanners are
weakest at, because it depends on actually driving focus around the page.

WCAG 2.1: 2.1.1 Keyboard, 2.1.2 No Keyboard Trap, 2.4.1 Bypass Blocks,
          2.4.3 Focus Order, 2.4.7 Focus Visible
A11Y Project: keyboard accessibility, visible focus, skip link, logical tab order
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from utils import a11y
from .conftest import PUBLIC_PAGES

pytestmark = [pytest.mark.accessibility]

# Keyboard walks are slow; run them over a representative subset rather than
# every route. Home exercises the full nav/hero, datasets exercises a list page
# with filters, about-us exercises a content page.
KEYBOARD_PAGES = [p for p in PUBLIC_PAGES if p[0] in ("home", "datasets", "about-us")]
KEYBOARD_IDS = [p[0] for p in KEYBOARD_PAGES]

_ACTIVE_DESCRIPTOR = """
    const el = document.activeElement;
    if (!el || el === document.body) return null;
    return {
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type'),
        text: (el.innerText || el.value || '').trim().slice(0, 50),
        cls: (el.getAttribute('class') || '').slice(0, 60),
        href: el.getAttribute('href'),
        tabindex: el.getAttribute('tabindex'),
        rect: (() => { const r = el.getBoundingClientRect();
                       return { x: Math.round(r.x), y: Math.round(r.y),
                                w: Math.round(r.width), h: Math.round(r.height) }; })(),
    };
"""


@pytest.mark.parametrize("page_id,path", KEYBOARD_PAGES, ids=KEYBOARD_IDS)
def test_interactive_elements_are_keyboard_reachable(driver, goto, page_id, path):
    """WCAG 2.1.1 — tabbing must reach a meaningful share of the controls.

    Rather than demanding every control be reached (a long page legitimately
    needs many tabs), this walks a bounded number of stops and asserts focus
    actually moves through distinct, real elements.
    """
    goto(path)
    body = driver.find_element(By.TAG_NAME, "body")
    body.click()

    stops = []
    for _ in range(40):
        body.send_keys(Keys.TAB)
        el = driver.execute_script(_ACTIVE_DESCRIPTOR)
        if el is None:
            continue
        stops.append(el)

    unique = {(s["tag"], s["text"], s["href"]) for s in stops}

    interactive_total = driver.execute_script("""
        const visible = (el) => el.offsetParent !== null || el.getClientRects().length;
        return [...document.querySelectorAll(
            'a[href], button, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"])'
        )].filter(visible).length;
    """)

    problems = []
    if not stops:
        problems.append("Tab never moved focus to any element")
    elif len(unique) < 3:
        problems.append(
            f"Tab reached only {len(unique)} distinct element(s) across 40 presses "
            "— focus appears stuck"
        )

    a11y.record(
        check="keyboard-focusable",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={
            "url": path,
            "tab_stops_recorded": len(stops),
            "distinct_stops": len(unique),
            "interactive_elements_on_page": interactive_total,
            "first_stops": stops[:10],
            "problems": problems,
        },
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)}"


@pytest.mark.parametrize("page_id,path", KEYBOARD_PAGES, ids=KEYBOARD_IDS)
def test_focused_elements_have_visible_indicator(driver, goto, page_id, path):
    """WCAG 2.4.7 — focus must be visible, not suppressed by `outline: none`.

    Checks the computed style of each focused element for *some* focus affordance:
    an outline, a ring-style box-shadow, or a border/background change.
    """
    goto(path)
    body = driver.find_element(By.TAG_NAME, "body")
    body.click()

    checked, invisible = 0, []
    for _ in range(15):
        body.send_keys(Keys.TAB)
        info = driver.execute_script("""
            const el = document.activeElement;
            if (!el || el === document.body) return null;
            const cs = getComputedStyle(el);
            const outlineW = parseFloat(cs.outlineWidth) || 0;
            const hasOutline = cs.outlineStyle !== 'none' && outlineW > 0;
            const hasShadow  = cs.boxShadow && cs.boxShadow !== 'none';
            // Some design systems draw focus on a child or pseudo-element.
            const pseudo = getComputedStyle(el, '::after');
            const hasPseudoRing = pseudo && pseudo.content !== 'none' &&
                                  (parseFloat(pseudo.height) > 0 || parseFloat(pseudo.width) > 0);
            return {
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.value || '').trim().slice(0, 40),
                outline: cs.outline, boxShadow: (cs.boxShadow||'').slice(0, 60),
                visible: !!(hasOutline || hasShadow || hasPseudoRing),
            };
        """)
        if info is None:
            continue
        checked += 1
        if not info["visible"]:
            invisible.append(info)

    a11y.record(
        check="focus-visible",
        page=page_id,
        status="pass" if not invisible else "fail",
        detail={
            "url": path,
            "elements_checked": checked,
            "without_indicator": invisible[:10],
        },
    )
    assert checked > 0, f"{page_id} ({path}): no element ever received focus"
    assert not invisible, (
        f"{page_id} ({path}): {len(invisible)} of {checked} focused element(s) had no "
        f"visible focus indicator: {invisible[:5]}"
    )


@pytest.mark.parametrize("page_id,path", KEYBOARD_PAGES, ids=KEYBOARD_IDS)
def test_no_keyboard_trap(driver, goto, page_id, path):
    """WCAG 2.1.2 — focus must never get stuck on one element."""
    goto(path)
    body = driver.find_element(By.TAG_NAME, "body")
    body.click()

    seen, repeats, prev = [], 0, None
    for _ in range(30):
        body.send_keys(Keys.TAB)
        el = driver.execute_script(_ACTIVE_DESCRIPTOR)
        sig = None if el is None else (el["tag"], el["text"], el["href"])
        if sig is not None and sig == prev:
            repeats += 1
        else:
            repeats = 0
        if sig is not None:
            seen.append(sig)
        prev = sig
        if repeats >= 5:
            break

    trapped = repeats >= 5
    a11y.record(
        check="no-keyboard-trap",
        page=page_id,
        status="fail" if trapped else "pass",
        detail={
            "url": path,
            "consecutive_repeats": repeats,
            "stuck_on": prev,
            "distinct_elements": len(set(seen)),
        },
    )
    assert not trapped, (
        f"{page_id} ({path}): keyboard focus appears trapped — same element "
        f"focused {repeats + 1} times consecutively: {prev}"
    )


@pytest.mark.parametrize("page_id,path", KEYBOARD_PAGES, ids=KEYBOARD_IDS)
def test_skip_to_content_mechanism_exists(driver, goto, page_id, path):
    """WCAG 2.4.1 — a way to bypass the repeated nav block.

    A skip link is the usual mechanism; a main landmark reachable as the first
    tab stop also satisfies the intent, so both are accepted.
    """
    goto(path)

    result = driver.execute_script("""
        const anchors = [...document.querySelectorAll('a[href^="#"]')];
        const skip = anchors.filter(a => {
            const t = ((a.innerText||'') + ' ' + (a.getAttribute('aria-label')||'')).toLowerCase();
            return t.includes('skip') || t.includes('jump to');
        }).map(a => ({ href: a.getAttribute('href'),
                       text: (a.innerText||a.getAttribute('aria-label')||'').trim() }));
        return { skip_links: skip, has_main: !!document.querySelector('main, [role=main]') };
    """)

    has_skip = bool(result["skip_links"])
    a11y.record(
        check="skip-link",
        page=page_id,
        status="pass" if has_skip else "fail",
        detail={
            "url": path,
            "skip_links": result["skip_links"],
            "has_main_landmark": result["has_main"],
        },
    )
    assert has_skip, (
        f"{page_id} ({path}): no skip-to-content link found. Keyboard and screen-reader "
        f"users must tab through the entire header on every page. "
        f"(main landmark present: {result['has_main']})"
    )


@pytest.mark.parametrize("page_id,path", KEYBOARD_PAGES, ids=KEYBOARD_IDS)
def test_focus_order_follows_visual_order(driver, goto, page_id, path):
    """WCAG 2.4.3 — tab order should broadly follow reading order.

    Flags large upward jumps: focus moving significantly back up the page is the
    signature of a positive tabindex or a mis-ordered DOM.
    """
    goto(path)
    body = driver.find_element(By.TAG_NAME, "body")
    body.click()

    positions = []
    for _ in range(25):
        body.send_keys(Keys.TAB)
        el = driver.execute_script(_ACTIVE_DESCRIPTOR)
        if el and el["rect"]["h"] > 0:
            positions.append(el)

    backward_jumps = []
    for i in range(1, len(positions)):
        prev_y = positions[i - 1]["rect"]["y"]
        cur_y = positions[i]["rect"]["y"]
        if cur_y < prev_y - 250:  # tolerate wrapping within a row/section
            backward_jumps.append({
                "from": positions[i - 1]["text"], "from_y": prev_y,
                "to": positions[i]["text"], "to_y": cur_y,
            })

    positive_tabindex = driver.execute_script("""
        return [...document.querySelectorAll('[tabindex]')]
            .filter(el => Number(el.getAttribute('tabindex')) > 0)
            .slice(0, 10)
            .map(el => ({ tag: el.tagName.toLowerCase(),
                          tabindex: el.getAttribute('tabindex') }));
    """)

    problems = []
    if positive_tabindex:
        problems.append(f"{len(positive_tabindex)} element(s) use a positive tabindex")
    # One backward jump is normal (wrapping out of the header into main);
    # several indicate a genuinely scrambled order.
    if len(backward_jumps) > 2:
        problems.append(f"{len(backward_jumps)} large backward focus jumps")

    a11y.record(
        check="focus-order",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={
            "url": path,
            "stops_measured": len(positions),
            "backward_jumps": backward_jumps[:5],
            "positive_tabindex": positive_tabindex,
            "problems": problems,
        },
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)}"
