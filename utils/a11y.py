"""
Accessibility testing helpers for the CivicDataSpace Selenium suite.

Two things live here:

1. `run_axe()` — injects the vendored axe-core bundle into the current page and
   runs it against the WCAG 2.0/2.1 A + AA rule tags. axe-core is vendored at
   `vendor/axe.min.js` rather than pulled from a CDN so scans are deterministic
   and work offline; `axe-selenium-python` is deliberately not used because its
   last release (2019) bundles an axe-core too old to carry the WCAG 2.1 rules.

2. `record()` — every accessibility test writes one JSON finding file into
   `reports/a11y/`. The report generator aggregates those files afterwards.
   Findings go to disk rather than a shared in-process structure because this
   suite runs under pytest-xdist, where a module-level collector populated in a
   worker is invisible to the controller.

Checklist coverage is tracked explicitly: every check declares the WCAG 2.1
success criteria and the A11Y Project checklist item it maps to, so the report
can show what was actually verified instead of just a pass/fail count.

References:
  - https://www.w3.org/TR/WCAG21/
  - https://www.a11yproject.com/checklist/
"""

import hashlib
import json
import os
import re
from pathlib import Path

# ─── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
AXE_BUNDLE = REPO_ROOT / "vendor" / "axe.min.js"
FINDINGS_DIR = REPO_ROOT / "reports" / "a11y"

# axe rule tags for WCAG 2.0 + 2.1, levels A and AA. "best-practice" is
# deliberately excluded: those rules are opinions, not conformance failures,
# and mixing them in makes a conformance report impossible to read.
WCAG_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

# Impact levels that fail a build. axe's "minor"/"moderate" findings are
# reported but not treated as blocking, matching how the Parakh suite gates.
BLOCKING_IMPACTS = ("critical", "serious")


# ─── Checklist registry ────────────────────────────────────────────────────────
#
# Maps each check id used by the tests to the standards it satisfies. Keeping
# this in one place means the report and the tests can never disagree about
# what a given check claims to cover.

CHECKS = {
    # Automated axe scans
    "axe-scan": {
        "title": "axe-core automated WCAG 2.1 AA scan",
        "wcag": ["Multiple (see per-violation tags)"],
        "a11y_project": "Run an automated accessibility checker",
    },
    # Structure / semantics
    "page-title": {
        "title": "Page has a unique, descriptive <title>",
        "wcag": ["2.4.2 Page Titled (A)"],
        "a11y_project": "Make sure the page has a title",
    },
    "html-lang": {
        "title": "<html> declares a valid lang attribute",
        "wcag": ["3.1.1 Language of Page (A)"],
        "a11y_project": "Set the language of the page",
    },
    "landmarks": {
        "title": "Page exposes main/nav/banner/contentinfo landmarks",
        "wcag": ["1.3.1 Info and Relationships (A)", "2.4.1 Bypass Blocks (A)"],
        "a11y_project": "Use landmarks to designate regions",
    },
    "heading-order": {
        "title": "Exactly one h1 and no skipped heading levels",
        "wcag": ["1.3.1 Info and Relationships (A)", "2.4.6 Headings and Labels (AA)"],
        "a11y_project": "Headings are in logical order",
    },
    "form-labels": {
        "title": "Every form control has an accessible name",
        "wcag": ["1.3.1 Info and Relationships (A)", "3.3.2 Labels or Instructions (A)", "4.1.2 Name, Role, Value (A)"],
        "a11y_project": "All inputs have an associated label",
    },
    # Perceivable
    "image-alt": {
        "title": "All images have alt text (or are marked decorative)",
        "wcag": ["1.1.1 Non-text Content (A)"],
        "a11y_project": "All images have alt text",
    },
    "color-contrast": {
        "title": "Text meets 4.5:1 (3:1 large) contrast ratio",
        "wcag": ["1.4.3 Contrast (Minimum) (AA)"],
        "a11y_project": "Check colour contrast",
    },
    "text-resize": {
        "title": "Content usable at 200% text size without loss",
        "wcag": ["1.4.4 Resize Text (AA)"],
        "a11y_project": "Text can be resized without breaking layout",
    },
    "reflow": {
        "title": "No horizontal scrolling at 320px width",
        "wcag": ["1.4.10 Reflow (AA)"],
        "a11y_project": "Content reflows to a single column",
    },
    "link-purpose": {
        "title": "Links have discernible, non-generic text",
        "wcag": ["2.4.4 Link Purpose (In Context) (A)"],
        "a11y_project": "Links are recognisable and descriptive",
    },
    # Operable / keyboard
    "keyboard-focusable": {
        "title": "All interactive controls are reachable by keyboard",
        "wcag": ["2.1.1 Keyboard (A)"],
        "a11y_project": "All functionality is keyboard accessible",
    },
    "focus-visible": {
        "title": "Focused elements have a visible focus indicator",
        "wcag": ["2.4.7 Focus Visible (AA)"],
        "a11y_project": "There is a visible focus indicator",
    },
    "no-keyboard-trap": {
        "title": "Keyboard focus is never trapped",
        "wcag": ["2.1.2 No Keyboard Trap (A)"],
        "a11y_project": "Keyboard focus is never trapped",
    },
    "skip-link": {
        "title": "A skip-to-content mechanism is available",
        "wcag": ["2.4.1 Bypass Blocks (A)"],
        "a11y_project": "Provide a skip link",
    },
    "focus-order": {
        "title": "Tab order follows a meaningful sequence",
        "wcag": ["2.4.3 Focus Order (A)"],
        "a11y_project": "Tab order is logical",
    },
    "target-size": {
        "title": "Interactive targets are large enough to activate",
        "wcag": ["2.5.5 Target Size (AAA, tracked as best practice)"],
        "a11y_project": "Touch targets are large enough",
    },
    # Accessibility Options widget (see tests/accessibility/test_a11y_006_widget.py)
    "widget-present": {
        "title": "Accessibility Options widget is available",
        "wcag": ["1.4.4 Resize Text (AA)", "1.4.8 Visual Presentation (AAA)"],
        "a11y_project": "Provide user-controllable display preferences",
    },
    "widget-control": {
        "title": "Accessibility Options control behaves as specified",
        "wcag": ["1.4.4 Resize Text (AA)", "1.4.3 Contrast (Minimum) (AA)", "2.1.1 Keyboard (A)"],
        "a11y_project": "Provide user-controllable display preferences",
    },
}


# ─── axe-core execution ────────────────────────────────────────────────────────

def _axe_source() -> str:
    if not AXE_BUNDLE.exists():
        raise FileNotFoundError(
            f"Vendored axe-core not found at {AXE_BUNDLE}. "
            "Re-add it with: curl -sSL -o vendor/axe.min.js "
            "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js"
        )
    return AXE_BUNDLE.read_text(encoding="utf-8")


def run_axe(driver, tags=None, include=None) -> dict:
    """Inject axe-core into the current page and run it.

    Returns the raw axe results dict (violations/passes/incomplete/inapplicable).

    axe is re-injected per call rather than cached on the driver because a page
    navigation wipes the JS context, and every caller here scans after
    navigating.
    """
    tags = tags or WCAG_AA_TAGS

    driver.execute_script(_axe_source())

    # axe.run is promise-based; execute_async_script bridges it back to Python.
    driver.set_script_timeout(120)
    script = """
        const done = arguments[arguments.length - 1];
        const tags = arguments[0];
        const include = arguments[1];
        const context = include ? include : document;
        axe.run(context, { runOnly: { type: 'tag', values: tags } })
           .then(r => done({ ok: true, results: r }))
           .catch(e => done({ ok: false, error: String(e) }));
    """
    outcome = driver.execute_async_script(script, tags, include)
    if not outcome.get("ok"):
        raise RuntimeError(f"axe-core failed to run: {outcome.get('error')}")
    return outcome["results"]


def blocking_violations(axe_results: dict) -> list:
    """Violations at critical/serious impact — the ones that fail a test."""
    return [
        v for v in axe_results.get("violations", [])
        if v.get("impact") in BLOCKING_IMPACTS
    ]


def summarize_violations(violations: list, limit: int = 12) -> str:
    """Human-readable one-line-per-violation summary for assertion messages."""
    if not violations:
        return "none"
    lines = []
    for v in violations[:limit]:
        nodes = v.get("nodes", [])
        target = ""
        if nodes:
            t = nodes[0].get("target", [])
            target = f" e.g. {t[0]}" if t else ""
        lines.append(
            f"[{v.get('impact')}] {v.get('id')}: {v.get('help')} "
            f"({len(nodes)} node{'s' if len(nodes) != 1 else ''}){target}"
        )
    if len(violations) > limit:
        lines.append(f"... and {len(violations) - limit} more")
    return "\n  ".join(lines)


# ─── Finding recorder ──────────────────────────────────────────────────────────

def record(check: str, page: str, status: str, detail=None, violations=None):
    """Write one accessibility finding to reports/a11y/ for the report generator.

    status: "pass" | "fail" | "not_implemented" | "skipped"
    """
    if check not in CHECKS:
        raise KeyError(f"Unknown accessibility check id {check!r}; add it to utils.a11y.CHECKS")

    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)

    meta = CHECKS[check]
    payload = {
        "check": check,
        "title": meta["title"],
        "wcag": meta["wcag"],
        "a11y_project": meta["a11y_project"],
        "page": page,
        "status": status,
        "detail": detail,
        "violations": _trim_violations(violations or []),
    }

    # Filename must be unique per (check, page) AND per xdist worker, or
    # parallel workers overwrite each other's findings.
    worker = os.getenv("PYTEST_XDIST_WORKER", "main")
    key = hashlib.sha1(f"{check}|{page}".encode()).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", f"{check}-{page}".lower()).strip("-")[:80]
    (FINDINGS_DIR / f"{slug}-{key}-{worker}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _trim_violations(violations: list) -> list:
    """Keep the report readable: drop axe's bulky per-node HTML payloads."""
    trimmed = []
    for v in violations:
        trimmed.append({
            "id": v.get("id"),
            "impact": v.get("impact"),
            "help": v.get("help"),
            "helpUrl": v.get("helpUrl"),
            "tags": [t for t in v.get("tags", []) if t.startswith("wcag")],
            "node_count": len(v.get("nodes", [])),
            "sample_targets": [
                n.get("target", [""])[0] for n in v.get("nodes", [])[:5]
            ],
        })
    return trimmed


def clear_findings():
    """Remove findings from previous runs so a report never mixes two runs."""
    if FINDINGS_DIR.exists():
        for f in FINDINGS_DIR.glob("*.json"):
            f.unlink()
