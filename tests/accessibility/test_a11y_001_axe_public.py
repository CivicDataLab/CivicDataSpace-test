"""
Automated axe-core WCAG 2.1 AA scans across the public (unauthenticated) pages.

One test per page so a failure names the page, and so a single bad page doesn't
mask the rest. Only critical/serious violations fail the test; minor/moderate
findings are still recorded and appear in ACCESSIBILITY_REPORT.md.

A11Y Project: "Run an automated accessibility checker"
WCAG 2.1: broad — each violation carries its own success-criterion tags.
"""

import pytest

from utils import a11y
from .conftest import PUBLIC_PAGES

pytestmark = [pytest.mark.accessibility]


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=[p[0] for p in PUBLIC_PAGES])
def test_public_page_has_no_critical_axe_violations(driver, goto, page_id, path):
    """Each public page must pass an axe WCAG 2.1 A/AA scan cleanly."""
    goto(path)

    results = a11y.run_axe(driver)
    blocking = a11y.blocking_violations(results)
    all_violations = results.get("violations", [])

    a11y.record(
        check="axe-scan",
        page=page_id,
        status="pass" if not blocking else "fail",
        detail={
            "url": path,
            "axe_version": results.get("testEngine", {}).get("version"),
            "passes": len(results.get("passes", [])),
            "violations_total": len(all_violations),
            "violations_blocking": len(blocking),
            "incomplete": len(results.get("incomplete", [])),
        },
        violations=all_violations,
    )

    assert not blocking, (
        f"{page_id} ({path}) has {len(blocking)} critical/serious "
        f"accessibility violation(s):\n  {a11y.summarize_violations(blocking)}"
    )


@pytest.mark.parametrize("page_id,path", PUBLIC_PAGES, ids=[p[0] for p in PUBLIC_PAGES])
def test_public_page_axe_scan_actually_ran(driver, goto, page_id, path):
    """Guard against a vacuously green scan.

    An axe run against a blank or error page returns zero violations and looks
    like a pass. Requiring a healthy number of passed rules proves real content
    was present and evaluated.
    """
    goto(path)
    results = a11y.run_axe(driver)

    passes = len(results.get("passes", []))
    assert passes >= 5, (
        f"{page_id} ({path}): axe only evaluated {passes} passing rule(s), which "
        "suggests the page did not render. Scan results for this page cannot be trusted."
    )
