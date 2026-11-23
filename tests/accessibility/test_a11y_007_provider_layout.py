"""
Layout of the provider dashboard sections at phone, tablet and desktop widths.

The page itself must not scroll sideways at any of the three (WCAG 1.4.10 asks
this at 320 CSS px; tablet and desktop catch tables and toolbars that outgrow
their column). A wide table may scroll inside its own container, so only the
document's width is measured.

WCAG 2.1: 1.4.10
"""

import re
from urllib.parse import urlparse

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from utils import a11y

pytestmark = [pytest.mark.accessibility]

_ENTITY_ROOT = re.compile(r"^https?://[^/]+(?:/[a-z]{2})?/dashboard/[^/]+/[^/?#]+")
SECTIONS = ["dataset", "usecases", "collaboratives", "aimodels", "publications", "charts", "events", "profile"]
VIEWPORTS = {"phone": (320, 900), "tablet": (768, 1024), "desktop": (1280, 800)}


@pytest.mark.parametrize("viewport", VIEWPORTS)
@pytest.mark.parametrize("section", SECTIONS)
def test_provider_section_does_not_scroll_sideways(provider_dashboard, driver, section, viewport):
    try:
        WebDriverWait(driver, 30).until(lambda d: _ENTITY_ROOT.match(d.current_url))
    except TimeoutException:
        pytest.fail(f"Not on an entity dashboard after login: {driver.current_url}")
    root = _ENTITY_ROOT.match(driver.current_url)
    original = driver.get_window_size()
    try:
        driver.set_window_size(*VIEWPORTS[viewport])
        driver.get(f"{root.group(0)}/{section}")
        WebDriverWait(driver, 20).until(lambda d: urlparse(d.current_url).path.rstrip("/").endswith(f"/{section}"))
        try:
            WebDriverWait(driver, 20).until(lambda d: d.execute_script(
                "return document.readyState === 'complete' && !/^\\s*Loading\\s*$/i.test((document.body.innerText||'').trim())"))
        except TimeoutException:
            pass
        measured = driver.execute_script("""
            const de = document.documentElement;
            const offenders = [...document.querySelectorAll('main *')]
                .filter(el => { const r = el.getBoundingClientRect(); return r.width && r.height && r.right > de.clientWidth + 4; })
                .slice(0, 8)
                .map(el => ({ tag: el.tagName.toLowerCase(), cls: (el.getAttribute('class')||'').slice(0, 40), right: Math.round(el.getBoundingClientRect().right) }));
            return { scrollW: de.scrollWidth, clientW: de.clientWidth, offenders };
        """)
        overflow = measured["scrollW"] > measured["clientW"] + 4
        a11y.record(check="reflow", page=f"provider-{section}-{viewport}",
                    status="fail" if overflow else "pass", detail={"url": driver.current_url, **measured})
        assert not overflow, (
            f"{section} at {viewport} ({VIEWPORTS[viewport][0]}px): the page scrolls sideways "
            f"(scrollWidth {measured['scrollW']} > clientWidth {measured['clientW']}). Offenders: {measured['offenders'][:4]}"
        )
    finally:
        driver.set_window_size(original["width"], original["height"])
