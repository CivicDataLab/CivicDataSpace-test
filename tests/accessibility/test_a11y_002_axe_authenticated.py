"""
axe-core scans behind login — the provider dashboard.

These are the densest, most form-heavy screens in the product and the ones a
public scan can never reach, so they get their own module. They reuse the root
conftest's `provider_dashboard` fixture for login.

WCAG 2.1 A/AA. A11Y Project: "Run an automated accessibility checker" (authenticated views)
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import a11y
from .conftest import PROVIDER_SECTIONS

pytestmark = [pytest.mark.accessibility]


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


def test_provider_dashboard_has_no_critical_axe_violations(provider_dashboard, driver):
    """The provider My Dashboard landing view must scan clean."""
    blocking = _scan_and_record(driver, "dashboard", driver.current_url)
    assert not blocking, (
        f"Provider dashboard has {len(blocking)} critical/serious violation(s):\n  "
        f"{a11y.summarize_violations(blocking)}"
    )


@pytest.mark.parametrize(
    "section_id,nav_label", PROVIDER_SECTIONS, ids=[s[0] for s in PROVIDER_SECTIONS]
)
def test_provider_section_has_no_critical_axe_violations(
    provider_dashboard, driver, section_id, nav_label
):
    """Each provider dashboard section must scan clean.

    Sections are reached by clicking the sidebar nav rather than by URL, because
    the real URLs embed a per-user slug that differs between test accounts.
    """
    link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//span[normalize-space()={nav_label!r}]"
                       f" | //a[normalize-space()={nav_label!r}]")
        ),
        message=f"Could not find the {nav_label!r} sidebar link",
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
    driver.execute_script("arguments[0].click();", link)

    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # Let the section's data query resolve so the scan sees real content.
    try:
        WebDriverWait(driver, 20).until(
            lambda d: not d.execute_script(
                "return /^\\s*Loading\\s*$/i.test((document.body.innerText||'').trim())"
            )
        )
    except Exception:
        pass

    blocking = _scan_and_record(driver, section_id, driver.current_url)
    assert not blocking, (
        f"Provider '{nav_label}' section has {len(blocking)} critical/serious "
        f"violation(s):\n  {a11y.summarize_violations(blocking)}"
    )
