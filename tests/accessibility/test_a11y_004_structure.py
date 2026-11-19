"""
Document structure and semantics checks.

These cover the A11Y Project checklist items that axe either cannot judge on its
own or only partially covers (axe flags a missing h1, but not a heading level
skipped halfway down the page; it flags a missing lang, but not a malformed one).

WCAG 2.1: 1.3.1, 2.4.1, 2.4.2, 2.4.4, 2.4.6, 3.1.1, 3.3.2, 4.1.2
"""

import pytest

from utils import a11y
from .conftest import PUBLIC_PAGES

pytestmark = [pytest.mark.accessibility]

PAGE_IDS = [p[0] for p in PUBLIC_PAGES]


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_page_has_descriptive_title(driver, goto, page_id, path):
    """WCAG 2.4.2 — every page needs a non-empty, meaningful <title>."""
    goto(path)
    title = (driver.title or "").strip()

    problems = []
    if not title:
        problems.append("title is empty")
    elif len(title) < 3:
        problems.append(f"title {title!r} is too short to be descriptive")
    if title.lower() in ("untitled", "react app", "next app", "document"):
        problems.append(f"title {title!r} is a placeholder")

    a11y.record(
        check="page-title",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={"url": path, "title": title, "problems": problems},
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)}"


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_html_has_valid_lang(driver, goto, page_id, path):
    """WCAG 3.1.1 — <html lang> must be present and a plausible language tag."""
    goto(path)
    lang = driver.execute_script(
        "return document.documentElement.getAttribute('lang');"
    )

    problems = []
    if not lang or not lang.strip():
        problems.append("<html> has no lang attribute")
    elif not _looks_like_bcp47(lang.strip()):
        problems.append(f"lang={lang!r} is not a valid BCP-47 language tag")

    a11y.record(
        check="html-lang",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={"url": path, "lang": lang, "problems": problems},
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)}"


def _looks_like_bcp47(tag: str) -> bool:
    import re
    return bool(re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*", tag))


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_page_exposes_landmarks(driver, goto, page_id, path):
    """WCAG 1.3.1 / 2.4.1 — screen-reader users navigate by landmark regions."""
    goto(path)
    found = driver.execute_script("""
        const q = (sel) => document.querySelectorAll(sel).length;
        return {
            main:        q('main, [role="main"]'),
            nav:         q('nav, [role="navigation"]'),
            banner:      q('header, [role="banner"]'),
            contentinfo: q('footer, [role="contentinfo"]'),
        };
    """)

    problems = []
    if found["main"] == 0:
        problems.append("no <main> / role=main landmark")
    if found["main"] > 1:
        problems.append(f"{found['main']} main landmarks (expected exactly 1)")
    if found["nav"] == 0:
        problems.append("no <nav> / role=navigation landmark")

    a11y.record(
        check="landmarks",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={"url": path, "landmarks": found, "problems": problems},
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)}"


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_heading_hierarchy_is_sane(driver, goto, page_id, path):
    """WCAG 1.3.1 / 2.4.6 — one h1, no skipped levels, no empty headings."""
    goto(path)
    headings = driver.execute_script("""
        return [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')]
            .filter(h => h.offsetParent !== null || h.getClientRects().length)
            .map(h => ({ level: Number(h.tagName[1]), text: (h.innerText||'').trim() }));
    """)

    problems = []
    levels = [h["level"] for h in headings]

    if not headings:
        problems.append("page has no headings at all")
    else:
        h1_count = levels.count(1)
        if h1_count == 0:
            problems.append("no <h1>")
        elif h1_count > 1:
            problems.append(f"{h1_count} <h1> elements (expected exactly 1)")

        for i in range(1, len(levels)):
            jump = levels[i] - levels[i - 1]
            if jump > 1:
                problems.append(
                    f"heading level jumps h{levels[i-1]} -> h{levels[i]} "
                    f"at {headings[i]['text'][:40]!r}"
                )

        empty = [h for h in headings if not h["text"]]
        if empty:
            problems.append(f"{len(empty)} empty heading element(s)")

    a11y.record(
        check="heading-order",
        page=page_id,
        status="pass" if not problems else "fail",
        detail={"url": path, "headings": headings[:25], "problems": problems},
    )
    assert not problems, f"{page_id} ({path}): {'; '.join(problems)}"


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_form_controls_have_accessible_names(driver, goto, page_id, path):
    """WCAG 1.3.1 / 3.3.2 / 4.1.2 — every visible control needs a name."""
    goto(path)
    unlabelled = driver.execute_script("""
        const visible = (el) => el.offsetParent !== null || el.getClientRects().length;
        const named = (el) => {
            if (el.getAttribute('aria-label')?.trim()) return true;
            const lb = el.getAttribute('aria-labelledby');
            if (lb && lb.split(/\\s+/).some(id => document.getElementById(id))) return true;
            if (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) return true;
            if (el.closest('label')) return true;
            if (el.getAttribute('title')?.trim()) return true;
            // Buttons may be named by their own content
            if (['BUTTON','A'].includes(el.tagName) && (el.innerText||'').trim()) return true;
            return false;
        };
        return [...document.querySelectorAll('input, select, textarea, button')]
            .filter(el => el.type !== 'hidden')
            .filter(visible)
            .filter(el => !named(el))
            .slice(0, 25)
            .map(el => ({
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type'),
                name: el.getAttribute('name'),
                cls: (el.getAttribute('class')||'').slice(0, 60),
            }));
    """)

    a11y.record(
        check="form-labels",
        page=page_id,
        status="pass" if not unlabelled else "fail",
        detail={"url": path, "unlabelled": unlabelled},
    )
    assert not unlabelled, (
        f"{page_id} ({path}): {len(unlabelled)} form control(s) without an "
        f"accessible name: {unlabelled}"
    )


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=PAGE_IDS)
def test_links_have_discernible_purpose(driver, goto, page_id, path):
    """WCAG 2.4.4 — links need text; generic text is flagged as a warning."""
    goto(path)
    data = driver.execute_script("""
        const visible = (el) => el.offsetParent !== null || el.getClientRects().length;
        const generic = ['click here','here','read more','more','link','this','learn more'];
        const links = [...document.querySelectorAll('a[href]')].filter(visible);
        const name = (a) =>
            (a.innerText||'').trim() ||
            (a.getAttribute('aria-label')||'').trim() ||
            (a.querySelector('img')?.getAttribute('alt')||'').trim() ||
            (a.getAttribute('title')||'').trim();
        return {
            empty: links.filter(a => !name(a))
                        .slice(0,15)
                        .map(a => ({ href: a.getAttribute('href'),
                                     cls: (a.getAttribute('class')||'').slice(0,60) })),
            generic: links.filter(a => generic.includes(name(a).toLowerCase()))
                          .slice(0,15)
                          .map(a => ({ href: a.getAttribute('href'), text: name(a) })),
            total: links.length,
        };
    """)

    a11y.record(
        check="link-purpose",
        page=page_id,
        status="pass" if not data["empty"] else "fail",
        detail={
            "url": path,
            "total_links": data["total"],
            "empty_links": data["empty"],
            "generic_links": data["generic"],
        },
    )
    assert not data["empty"], (
        f"{page_id} ({path}): {len(data['empty'])} link(s) with no discernible "
        f"text: {data['empty']}"
    )
