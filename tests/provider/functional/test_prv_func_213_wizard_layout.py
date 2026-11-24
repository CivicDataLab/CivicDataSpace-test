# tests/provider/functional/test_prv_func_213_wizard_layout.py
#
# The create/edit wizards at phone, tablet and desktop widths: no step may
# scroll the page sideways (a form, table or step bar that outgrows its column).
# One draft of each kind is made through the API and deleted at teardown; the
# test only opens its steps by URL.

import uuid

import pytest

from tests.provider.functional.conftest import DASHBOARD_BASE

pytestmark = pytest.mark.functional

VIEWPORTS = {"phone": (320, 900), "tablet": (768, 1024), "desktop": (1280, 800)}
STEPS = {
    "dataset": ["metadata", "resources"],
    "usecase": ["details"],
    "publication": ["files", "details", "publish"],
}
OVERFLOW = """
    const de = document.documentElement;
    const offenders = [...document.querySelectorAll('main *')]
        .filter(el => { const r = el.getBoundingClientRect(); return r.width && r.height && r.right > window.innerWidth + 4; })
        .slice(0, 6).map(el => el.tagName.toLowerCase() + '.' + (el.getAttribute('class')||'').slice(0, 30) + '@' + Math.round(el.getBoundingClientRect().right));
    return { scrollW: de.scrollWidth, width: window.innerWidth, offenders };
"""


def _settle(driver):
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait
    try:
        WebDriverWait(driver, 20).until(lambda d: d.execute_script(
            "return document.readyState === 'complete' && !/^\\s*Loading\\s*$/i.test((document.body.innerText||'').trim())"))
    except TimeoutException:
        pass


@pytest.mark.timeout(900)
def test_prv_func_213_no_wizard_step_scrolls_sideways(driver, open_listing, qa_drafts, provider_api, cleanup):
    open_listing("individual", "Datasets")
    base = DASHBOARD_BASE.search(driver.current_url).group(1)
    urls = {}
    for step in STEPS["dataset"]:
        urls[f"dataset/{step}"] = qa_drafts.create("data", driver).rsplit("/", 1)[0] + f"/{step}"
    urls_uc = qa_drafts.create("uc", driver)
    urls.update({f"usecase/{step}": urls_uc.rsplit("/", 1)[0] + f"/{step}" for step in STEPS["usecase"]})
    pid = provider_api.create_draft("publication", f"zz-auto-wl-{uuid.uuid4().hex[:8]}")
    cleanup.track("publication", pid, None)
    urls.update({f"publication/{step}": f"{base}/publications/edit/{pid}/{step}" for step in STEPS["publication"]})

    original = driver.get_window_size()
    problems = []
    try:
        for viewport, size in VIEWPORTS.items():
            driver.set_window_size(*size)
            for name, url in urls.items():
                driver.get(url)
                _settle(driver)
                measured = driver.execute_script(OVERFLOW)
                if measured["scrollW"] > measured["width"] + 4:
                    problems.append(f"{name} at {viewport} ({size[0]}px): scrollWidth {measured['scrollW']} > {measured['width']}; {measured['offenders'][:3]}")
    finally:
        driver.set_window_size(original["width"], original["height"])
    assert not problems, "Wizard steps scroll sideways:\n" + "\n".join(problems)
