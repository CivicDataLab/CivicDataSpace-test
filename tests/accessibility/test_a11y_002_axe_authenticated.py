"""
axe-core scans behind login — the provider dashboard.

These are the densest, most form-heavy screens in the product and the ones a
public scan can never reach, so they get their own module. They reuse the root
conftest's `provider_dashboard` fixture for login.

WCAG 2.1 A/AA. A11Y Project: "Run an automated accessibility checker" (authenticated views)
"""

import re
from urllib.parse import urlparse

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from utils import a11y
from .conftest import PROVIDER_SECTIONS

pytestmark = [pytest.mark.accessibility]

# https://host[/locale]/dashboard/<entityType>/<slug>
_ENTITY_ROOT = re.compile(r"^https?://[^/]+(?:/[a-z]{2})?/dashboard/[^/]+/[^/?#]+")


def _scan_and_record(driver, page_id: str, url_hint: str):
    results = a11y.run_axe(driver)
    blocking = a11y.blocking_violations(results)
    a11y.record(
        check="axe-scan",
        page=f"provider-{page_id}",
        status="pass" if not blocking else "fail",
        detail={
            "url": url_hint,
            "authenticated": True,
            "axe_version": results.get("testEngine", {}).get("version"),
            "passes": len(results.get("passes", [])),
            "violations_total": len(results.get("violations", [])),
            "violations_blocking": len(blocking),
        },
        violations=results.get("violations", []),
    )
    return blocking


def _wait_for_content(driver):
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # Let the page's data query resolve so the scan sees real content.
    try:
        WebDriverWait(driver, 20).until(
            lambda d: not d.execute_script(
                "return /^\\s*Loading\\s*$/i.test((document.body.innerText||'').trim())"
            )
        )
    except TimeoutException:
        pass


def test_provider_dashboard_has_no_critical_axe_violations(provider_dashboard, driver):
    """The User Dashboard hub (/dashboard: My Dashboard + organisation cards) must scan clean."""
    u = urlparse(driver.current_url)
    driver.get(f"{u.scheme}://{u.netloc}/dashboard")
    WebDriverWait(driver, 20).until(lambda d: urlparse(d.current_url).path.rstrip("/").endswith("/dashboard"))
    _wait_for_content(driver)
    blocking = _scan_and_record(driver, "dashboard", driver.current_url)
    assert not blocking, (
        f"Provider dashboard has {len(blocking)} critical/serious violation(s):\n  "
        f"{a11y.summarize_violations(blocking)}"
    )


@pytest.mark.parametrize(
    "section_id,path", PROVIDER_SECTIONS, ids=[s[0] for s in PROVIDER_SECTIONS]
)
def test_provider_section_has_no_critical_axe_violations(
    provider_dashboard, driver, section_id, path
):
    """Each provider dashboard section must scan clean.

    Navigates by URL: a JS click on the sidebar never left the datasets view, so
    every section used to scan the same page (/dashboard/self/<slug>/dataset).
    """
    root = _ENTITY_ROOT.match(driver.current_url)
    assert root, f"Not on an entity dashboard after login: {driver.current_url}"
    driver.get(f"{root.group(0)}/{path}")
    WebDriverWait(driver, 20).until(
        lambda d: urlparse(d.current_url).path.rstrip("/").endswith(f"/{path}"),
        message=f"Did not land on the {path!r} section (at {driver.current_url})",
    )
    _wait_for_content(driver)

    blocking = _scan_and_record(driver, section_id, driver.current_url)
    assert not blocking, (
        f"Provider '{section_id}' section has {len(blocking)} critical/serious "
        f"violation(s):\n  {a11y.summarize_violations(blocking)}"
    )
