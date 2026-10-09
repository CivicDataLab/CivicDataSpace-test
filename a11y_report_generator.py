#!/usr/bin/env python
"""
Build ACCESSIBILITY_REPORT.md (and .html) from the findings written by the
accessibility suite into reports/a11y/.

Run automatically by conftest.pytest_sessionfinish after an accessibility run,
or by hand:

    python a11y_report_generator.py

The report is organised around the two checklists the suite is written against:
  - WCAG 2.1 success criteria      https://www.w3.org/TR/WCAG21/
  - The A11Y Project checklist     https://www.a11yproject.com/checklist/
"""

import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FINDINGS_DIR = REPO_ROOT / "reports" / "a11y"
MD_OUT = REPO_ROOT / "ACCESSIBILITY_REPORT.md"
HTML_OUT = REPO_ROOT / "ACCESSIBILITY_REPORT.html"

STATUS_ICON = {
    "pass": "✅",
    "fail": "❌",
    "not_implemented": "🚧",
    "skipped": "⏭️",
}


def load_findings() -> list:
    if not FINDINGS_DIR.exists():
        return []
    out = []
    for f in sorted(FINDINGS_DIR.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:  # a truncated file shouldn't kill the report
            print(f"⚠️  skipping unreadable finding {f.name}: {e}")
    return out


def build_markdown(findings: list) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    by_status = defaultdict(list)
    for f in findings:
        by_status[f["status"]].append(f)

    passed = len(by_status["pass"])
    failed = len(by_status["fail"])
    pending = len(by_status["not_implemented"])
    total = len(findings)

    L = []
    L.append("# CivicDataSpace — Accessibility Report")
    L.append("")
    L.append(f"_Generated {now}_")
    L.append("")
    L.append("Standards this suite is written against:")
    L.append("")
    L.append("- [WCAG 2.1](https://www.w3.org/TR/WCAG21/) — Level A and AA")
    L.append("- [The A11Y Project checklist](https://www.a11yproject.com/checklist/)")
    L.append("- Accessibility Options widget specification (13 controls)")
    L.append("")

    # ── Summary ────────────────────────────────────────────────────────────
    L.append("## Summary")
    L.append("")
    L.append("| Result | Count |")
    L.append("|---|---:|")
    L.append(f"| ✅ Passed | {passed} |")
    L.append(f"| ❌ Failed | {failed} |")
    L.append(f"| 🚧 Not implemented | {pending} |")
    L.append(f"| **Total checks** | **{total}** |")
    L.append("")

    if total == 0:
        L.append("> No findings recorded. Run the suite first:")
        L.append("> `pytest tests/accessibility -m accessibility`")
        L.append("")
        return "\n".join(L)

    if failed:
        L.append(f"**{failed} check(s) failed.** See _Failures_ below.")
    else:
        L.append("**No conformance failures recorded.**")
    L.append("")

    # ── Failures ───────────────────────────────────────────────────────────
    if by_status["fail"]:
        L.append("## Failures")
        L.append("")
        for f in sorted(by_status["fail"], key=lambda x: (x["check"], x["page"])):
            L.append(f"### ❌ {f['title']} — `{f['page']}`")
            L.append("")
            L.append(f"- **WCAG:** {', '.join(f['wcag'])}")
            L.append(f"- **A11Y Project:** {f['a11y_project']}")
            detail = f.get("detail") or {}
            if detail.get("url"):
                L.append(f"- **Page:** `{detail['url']}`")
            for p in detail.get("problems", []) or []:
                L.append(f"- ⚠️ {p}")
            if f.get("violations"):
                L.append("")
                L.append("| Rule | Impact | Nodes | WCAG tags | Help |")
                L.append("|---|---|---:|---|---|")
                for v in f["violations"]:
                    tags = ", ".join(v.get("tags", [])) or "—"
                    L.append(
                        f"| `{v['id']}` | {v.get('impact') or '—'} | {v.get('node_count', 0)} "
                        f"| {tags} | [{v.get('help','')}]({v.get('helpUrl','')}) |"
                    )
            L.append("")

    # ── Outstanding / not implemented ──────────────────────────────────────
    if by_status["not_implemented"]:
        L.append("## Outstanding — not yet implemented")
        L.append("")
        L.append(
            "These are **not test errors**. The functionality does not exist on the "
            "deployment under test, so the checks are recorded as pending rather than "
            "passed. They become live checks as soon as the feature ships."
        )
        L.append("")
        note = next(
            (f["detail"].get("note") for f in by_status["not_implemented"]
             if (f.get("detail") or {}).get("note")),
            None,
        )
        if note:
            L.append(f"> {note}")
            L.append("")
        L.append("| Check | Item | WCAG |")
        L.append("|---|---|---|")
        for f in sorted(by_status["not_implemented"], key=lambda x: x["page"]):
            detail = f.get("detail") or {}
            item = detail.get("control") or f["page"]
            L.append(f"| {f['title']} | {item} | {', '.join(f['wcag'])} |")
        L.append("")

    # ── Coverage by WCAG criterion ─────────────────────────────────────────
    L.append("## Coverage by WCAG 2.1 success criterion")
    L.append("")
    by_sc = defaultdict(lambda: {"pass": 0, "fail": 0, "not_implemented": 0, "skipped": 0})
    for f in findings:
        for sc in f["wcag"]:
            by_sc[sc][f["status"]] = by_sc[sc].get(f["status"], 0) + 1

    L.append("| Success criterion | ✅ | ❌ | 🚧 |")
    L.append("|---|---:|---:|---:|")
    for sc in sorted(by_sc):
        c = by_sc[sc]
        L.append(f"| {sc} | {c['pass']} | {c['fail']} | {c['not_implemented']} |")
    L.append("")

    # ── Coverage by A11Y Project item ──────────────────────────────────────
    L.append("## Coverage by A11Y Project checklist item")
    L.append("")
    by_item = defaultdict(lambda: {"pass": 0, "fail": 0, "not_implemented": 0, "skipped": 0})
    for f in findings:
        by_item[f["a11y_project"]][f["status"]] += 1

    L.append("| Checklist item | ✅ | ❌ | 🚧 |")
    L.append("|---|---:|---:|---:|")
    for item in sorted(by_item):
        c = by_item[item]
        L.append(f"| {item} | {c['pass']} | {c['fail']} | {c['not_implemented']} |")
    L.append("")

    # ── Per-page matrix ────────────────────────────────────────────────────
    L.append("## Results by page")
    L.append("")
    pages = sorted({f["page"] for f in findings})
    checks = sorted({f["check"] for f in findings})
    matrix = {(f["page"], f["check"]): f["status"] for f in findings}

    L.append("| Page | " + " | ".join(checks) + " |")
    L.append("|---" * (len(checks) + 1) + "|")
    for page in pages:
        row = [page]
        for check in checks:
            st = matrix.get((page, check))
            row.append(STATUS_ICON.get(st, "·") if st else "·")
        L.append("| " + " | ".join(row) + " |")
    L.append("")
    L.append("Legend: ✅ pass · ❌ fail · 🚧 not implemented · · not applicable to this page")
    L.append("")

    # ── Passed detail ──────────────────────────────────────────────────────
    L.append("## Passed checks")
    L.append("")
    L.append("| Check | Page | WCAG |")
    L.append("|---|---|---|")
    for f in sorted(by_status["pass"], key=lambda x: (x["check"], x["page"])):
        L.append(f"| {f['title']} | `{f['page']}` | {', '.join(f['wcag'])} |")
    L.append("")

    return "\n".join(L)


STATUS_LABEL = {
    "pass": "Pass",
    "fail": "Fail",
    "not_implemented": "Not implemented",
    "skipped": "Skipped",
}

# axe impact -> badge class, for the per-violation rows inside a failure card.
IMPACT_CLASS = {
    "critical": "sev-critical",
    "serious": "sev-serious",
    "moderate": "sev-moderate",
    "minor": "sev-minor",
}


def _e(s) -> str:
    """HTML-escape, tolerating None."""
    return html.escape(str(s)) if s is not None else ""


def _bar(passed: int, failed: int, pending: int) -> str:
    """Inline three-segment progress bar (pass/fail/pending) for coverage rows."""
    total = passed + failed + pending
    if total == 0:
        return '<div class="bar"><div class="bar-empty"></div></div>'
    seg = lambda n, cls: f'<div class="bar-{cls}" style="width:{n / total * 100:.2f}%"></div>' if n else ""
    return (
        '<div class="bar" role="img" '
        f'aria-label="{passed} passed, {failed} failed, {pending} pending">'
        + seg(passed, "pass") + seg(failed, "fail") + seg(pending, "pending")
        + "</div>"
    )


def _violations_table(violations: list) -> str:
    if not violations:
        return ""
    rows = []
    for v in violations:
        impact = (v.get("impact") or "").lower()
        badge_cls = IMPACT_CLASS.get(impact, "sev-minor")
        tags = ", ".join(v.get("tags", [])) or "—"
        samples = v.get("sample_targets") or []
        sample_html = (
            "<br>".join(f'<code>{_e(s)}</code>' for s in samples[:3])
            if samples else ""
        )
        help_url = v.get("helpUrl") or "#"
        rows.append(f"""
          <tr>
            <td><code>{_e(v.get('id'))}</code></td>
            <td><span class="badge {badge_cls}">{_e(v.get('impact') or '—')}</span></td>
            <td>{v.get('node_count', 0)}</td>
            <td class="mono small">{_e(tags)}</td>
            <td><a href="{_e(help_url)}" target="_blank" rel="noopener">{_e(v.get('help',''))}</a>
                {f'<div class="small muted">{sample_html}</div>' if sample_html else ''}</td>
          </tr>""")
    return f"""
        <table class="violations">
          <thead><tr><th>Rule</th><th>Impact</th><th>Nodes</th><th>WCAG tags</th><th>Help</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>"""


def _failure_card(f: dict) -> str:
    detail = f.get("detail") or {}
    problems = detail.get("problems") or []
    page_url = detail.get("url")
    bullets = "".join(f"<li>{_e(p)}</li>" for p in problems)
    return f"""
      <article class="card fail-card">
        <header>
          <span class="badge sev-fail">FAIL</span>
          <h3>{_e(f['title'])}</h3>
          <span class="page-chip">{_e(f['page'])}</span>
        </header>
        <dl class="meta">
          <dt>WCAG</dt><dd>{_e(', '.join(f['wcag']))}</dd>
          <dt>A11Y Project</dt><dd>{_e(f['a11y_project'])}</dd>
          {f'<dt>Page</dt><dd><code>{_e(page_url)}</code></dd>' if page_url else ''}
        </dl>
        {f'<ul class="problems">{bullets}</ul>' if bullets else ''}
        {_violations_table(f.get('violations') or [])}
      </article>"""


def build_html(findings: list) -> str:
    """Self-contained HTML dashboard built directly from the findings data."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    by_status = defaultdict(list)
    for f in findings:
        by_status[f["status"]].append(f)

    passed = len(by_status["pass"])
    failed = len(by_status["fail"])
    pending = len(by_status["not_implemented"])
    total = len(findings)
    pass_rate = (passed / total * 100) if total else 0

    if total == 0:
        body = """
        <div class="empty">
          <p>No findings recorded yet.</p>
          <p>Run the suite first: <code>pytest tests/accessibility -m accessibility</code></p>
        </div>"""
        return _page_shell(now, body, sticky_nav="")

    # ── Failures ─────────────────────────────────────────────────────────
    failures_html = ""
    if by_status["fail"]:
        cards = "".join(
            _failure_card(f)
            for f in sorted(by_status["fail"], key=lambda x: (x["check"], x["page"]))
        )
        failures_html = f"""
        <section id="failures">
          <h2>Failures <span class="count-pill fail">{failed}</span></h2>
          {cards}
        </section>"""

    # ── Outstanding ──────────────────────────────────────────────────────
    outstanding_html = ""
    if by_status["not_implemented"]:
        note = next(
            (f["detail"].get("note") for f in by_status["not_implemented"]
             if (f.get("detail") or {}).get("note")),
            None,
        )
        rows = "".join(
            f"""<tr><td>{_e(f['title'])}</td>
                    <td>{_e((f.get('detail') or {}).get('control') or f['page'])}</td>
                    <td class="small">{_e(', '.join(f['wcag']))}</td></tr>"""
            for f in sorted(by_status["not_implemented"], key=lambda x: x["page"])
        )
        outstanding_html = f"""
        <section id="outstanding">
          <h2>Outstanding — not yet implemented <span class="count-pill pending">{pending}</span></h2>
          <p class="note">These are <strong>not test errors</strong>. The functionality does not
             exist on the deployment under test, so the checks are recorded as pending rather
             than passed. They become live checks as soon as the feature ships.</p>
          {f'<blockquote>{_e(note)}</blockquote>' if note else ''}
          <table class="plain">
            <thead><tr><th>Check</th><th>Item</th><th>WCAG</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>"""

    # ── Coverage by WCAG ─────────────────────────────────────────────────
    by_sc = defaultdict(lambda: {"pass": 0, "fail": 0, "not_implemented": 0})
    for f in findings:
        for sc in f["wcag"]:
            by_sc[sc][f["status"]] = by_sc[sc].get(f["status"], 0) + 1
    sc_rows = "".join(
        f"""<tr><td>{_e(sc)}</td>
                <td class="num">{c['pass']}</td><td class="num">{c['fail']}</td>
                <td class="num">{c['not_implemented']}</td>
                <td>{_bar(c['pass'], c['fail'], c['not_implemented'])}</td></tr>"""
        for sc, c in sorted(by_sc.items())
    )

    # ── Coverage by A11Y Project item ───────────────────────────────────
    by_item = defaultdict(lambda: {"pass": 0, "fail": 0, "not_implemented": 0})
    for f in findings:
        by_item[f["a11y_project"]][f["status"]] += 1
    item_rows = "".join(
        f"""<tr><td>{_e(item)}</td>
                <td class="num">{c['pass']}</td><td class="num">{c['fail']}</td>
                <td class="num">{c['not_implemented']}</td>
                <td>{_bar(c['pass'], c['fail'], c['not_implemented'])}</td></tr>"""
        for item, c in sorted(by_item.items())
    )

    # ── Per-page matrix ──────────────────────────────────────────────────
    pages = sorted({f["page"] for f in findings})
    checks = sorted({f["check"] for f in findings})
    matrix = {(f["page"], f["check"]): f["status"] for f in findings}
    STATUS_CELL = {
        "pass": '<span class="cell pass" title="Pass">✓</span>',
        "fail": '<span class="cell fail" title="Fail">✕</span>',
        "not_implemented": '<span class="cell pending" title="Not implemented">…</span>',
    }
    header_cells = "".join(f"<th>{_e(c)}</th>" for c in checks)
    page_rows = "".join(
        f"<tr><th>{_e(page)}</th>"
        + "".join(
            f"<td>{STATUS_CELL.get(matrix.get((page, check)), '<span class=\"cell na\">·</span>')}</td>"
            for check in checks
        )
        + "</tr>"
        for page in pages
    )

    # ── Passed checks ────────────────────────────────────────────────────
    passed_rows = "".join(
        f"""<tr><td>{_e(f['title'])}</td><td><code>{_e(f['page'])}</code></td>
                <td class="small">{_e(', '.join(f['wcag']))}</td></tr>"""
        for f in sorted(by_status["pass"], key=lambda x: (x["check"], x["page"]))
    )

    body = f"""
    <section class="summary">
      <div class="stat-grid">
        <div class="stat-card pass"><div class="stat-num">{passed}</div><div class="stat-label">Passed</div></div>
        <div class="stat-card fail"><div class="stat-num">{failed}</div><div class="stat-label">Failed</div></div>
        <div class="stat-card pending"><div class="stat-num">{pending}</div><div class="stat-label">Not implemented</div></div>
        <div class="stat-card total"><div class="stat-num">{total}</div><div class="stat-label">Total checks</div></div>
      </div>
      <div class="pass-rate-row">
        <div class="pass-rate-bar">{_bar(passed, failed, pending)}</div>
        <span class="pass-rate-label">{pass_rate:.0f}% passing</span>
      </div>
      <p class="verdict">{
        f'<strong class="fail-text">{failed} check(s) failed.</strong> See Failures below.'
        if failed else '<strong class="pass-text">No conformance failures recorded.</strong>'
      }</p>
    </section>

    {failures_html}
    {outstanding_html}

    <section id="coverage-wcag">
      <h2>Coverage by WCAG 2.1 success criterion</h2>
      <table class="plain cov">
        <thead><tr><th>Success criterion</th><th>✓</th><th>✕</th><th>…</th><th></th></tr></thead>
        <tbody>{sc_rows}</tbody>
      </table>
    </section>

    <section id="coverage-a11y">
      <h2>Coverage by A11Y Project checklist item</h2>
      <table class="plain cov">
        <thead><tr><th>Checklist item</th><th>✓</th><th>✕</th><th>…</th><th></th></tr></thead>
        <tbody>{item_rows}</tbody>
      </table>
    </section>

    <section id="by-page">
      <h2>Results by page</h2>
      <div class="table-scroll">
        <table class="matrix">
          <thead><tr><th>Page</th>{header_cells}</tr></thead>
          <tbody>{page_rows}</tbody>
        </table>
      </div>
      <p class="legend">
        <span class="cell pass">✓</span> pass &nbsp;
        <span class="cell fail">✕</span> fail &nbsp;
        <span class="cell pending">…</span> not implemented &nbsp;
        <span class="cell na">·</span> not applicable
      </p>
    </section>

    <section id="passed">
      <details>
        <summary><h2 style="display:inline">Passed checks <span class="count-pill pass">{passed}</span></h2></summary>
        <table class="plain">
          <thead><tr><th>Check</th><th>Page</th><th>WCAG</th></tr></thead>
          <tbody>{passed_rows}</tbody>
        </table>
      </details>
    </section>
    """

    nav = f"""
      <a href="#failures">Failures <span class="count-pill fail">{failed}</span></a>
      <a href="#outstanding">Outstanding <span class="count-pill pending">{pending}</span></a>
      <a href="#coverage-wcag">WCAG coverage</a>
      <a href="#coverage-a11y">A11Y Project coverage</a>
      <a href="#by-page">By page</a>
      <a href="#passed">Passed <span class="count-pill pass">{passed}</span></a>
    """
    return _page_shell(now, body, sticky_nav=nav)


def _page_shell(generated_at: str, body: str, sticky_nav: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CivicDataSpace — Accessibility Report</title>
<style>
{_CSS}
</style>
</head>
<body>
  <header class="page-header">
    <h1>CivicDataSpace — Accessibility Report</h1>
    <p class="generated">Generated {_e(generated_at)}</p>
    <p class="standards">
      <a href="https://www.w3.org/TR/WCAG21/" target="_blank" rel="noopener">WCAG 2.1 (A/AA)</a>
      &nbsp;·&nbsp;
      <a href="https://www.a11yproject.com/checklist/" target="_blank" rel="noopener">The A11Y Project checklist</a>
      &nbsp;·&nbsp;
      Accessibility Options widget spec (13 controls)
    </p>
  </header>
  {f'<nav class="toc">{sticky_nav}</nav>' if sticky_nav else ''}
  <main>
    {body}
  </main>
</body>
</html>"""


_CSS = """
  :root {
    color-scheme: light dark;
    --bg: #ffffff; --fg: #1a1d23; --muted: #6b7280; --border: #e2e5ea;
    --card-bg: #f8f9fb; --code-bg: #eef0f3;
    --pass: #1a8f4c; --pass-bg: #e7f7ee;
    --fail: #d1293d; --fail-bg: #fdeced;
    --pending: #b8710a; --pending-bg: #fdf3e2;
    --link: #2563eb;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #14161a; --fg: #e7e9ec; --muted: #9aa1ac; --border: #2a2e35;
      --card-bg: #1b1e24; --code-bg: #232830;
      --pass: #3ddc84; --pass-bg: #103822;
      --fail: #ff6b7a; --fail-bg: #3a1418;
      --pending: #f5b352; --pending-bg: #3a2a0d;
      --link: #7aa2ff;
    }
  }
  * { box-sizing: border-box; }
  body {
    background: var(--bg); color: var(--fg); margin: 0;
    font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  main { max-width: 1180px; margin: 0 auto; padding: 1.5rem 1.25rem 4rem; }
  a { color: var(--link); }
  code, .mono { font: 12.5px/1.4 "SF Mono", Menlo, Consolas, monospace; }
  code { background: var(--code-bg); padding: .1rem .35rem; border-radius: 4px; }
  .small { font-size: 12.5px; }
  .muted { color: var(--muted); }

  .page-header {
    background: var(--card-bg); border-bottom: 1px solid var(--border);
    padding: 1.5rem 1.25rem; text-align: center;
  }
  .page-header h1 { margin: 0 0 .25rem; font-size: 1.5rem; }
  .generated, .standards { margin: .2rem 0; color: var(--muted); font-size: 13.5px; }

  .toc {
    position: sticky; top: 0; z-index: 10; display: flex; gap: 1.25rem;
    flex-wrap: wrap; background: var(--bg); border-bottom: 1px solid var(--border);
    padding: .6rem 1.25rem; font-size: 13.5px; justify-content: center;
  }
  .toc a { text-decoration: none; color: var(--fg); display: inline-flex; align-items: center; gap: .3rem; }
  .toc a:hover { color: var(--link); }

  h2 { font-size: 1.15rem; margin: 2rem 0 .75rem; display: flex; align-items: center; gap: .5rem; }
  section { scroll-margin-top: 3rem; }

  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .75rem; margin-top: 1rem; }
  .stat-card { border: 1px solid var(--border); border-radius: 10px; padding: 1rem; text-align: center; background: var(--card-bg); }
  .stat-num { font-size: 2rem; font-weight: 700; line-height: 1; }
  .stat-label { color: var(--muted); font-size: 13px; margin-top: .35rem; }
  .stat-card.pass .stat-num { color: var(--pass); }
  .stat-card.fail .stat-num { color: var(--fail); }
  .stat-card.pending .stat-num { color: var(--pending); }

  .pass-rate-row { display: flex; align-items: center; gap: .75rem; margin-top: 1rem; }
  .pass-rate-bar { flex: 1; }
  .pass-rate-label { font-size: 13px; color: var(--muted); white-space: nowrap; }
  .verdict { margin-top: .75rem; }
  .fail-text { color: var(--fail); }
  .pass-text { color: var(--pass); }

  .bar { display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: var(--border); width: 100%; min-width: 60px; }
  .bar-pass { background: var(--pass); }
  .bar-fail { background: var(--fail); }
  .bar-pending { background: var(--pending); }
  .bar-empty { background: var(--border); width: 100%; }

  .count-pill {
    display: inline-block; min-width: 1.4em; text-align: center; padding: .05rem .45rem;
    border-radius: 999px; font-size: 12.5px; font-weight: 600;
  }
  .count-pill.pass { background: var(--pass-bg); color: var(--pass); }
  .count-pill.fail { background: var(--fail-bg); color: var(--fail); }
  .count-pill.pending { background: var(--pending-bg); color: var(--pending); }

  .badge { display: inline-block; padding: .1rem .5rem; border-radius: 999px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .03em; }
  .badge.sev-fail { background: var(--fail-bg); color: var(--fail); }
  .badge.sev-critical { background: var(--fail-bg); color: var(--fail); }
  .badge.sev-serious { background: var(--pending-bg); color: var(--pending); }
  .badge.sev-moderate { background: var(--code-bg); color: var(--muted); }
  .badge.sev-minor { background: var(--code-bg); color: var(--muted); }

  .card { border: 1px solid var(--border); border-left: 4px solid var(--fail); border-radius: 10px;
          background: var(--card-bg); padding: 1rem 1.1rem; margin-bottom: 1rem; }
  .card header { display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }
  .card h3 { margin: 0; font-size: 1rem; flex: 1; min-width: 200px; }
  .page-chip { background: var(--code-bg); border-radius: 6px; padding: .1rem .5rem; font-size: 12px; font-family: monospace; }

  .meta { display: grid; grid-template-columns: max-content 1fr; gap: .2rem .75rem; margin: .6rem 0; font-size: 13.5px; }
  .meta dt { color: var(--muted); }
  .meta dd { margin: 0; }

  .problems { margin: .5rem 0 0; padding-left: 1.2rem; font-size: 13.5px; }
  .problems li { margin: .2rem 0; }

  table { border-collapse: collapse; width: 100%; margin: .5rem 0; }
  table.plain th, table.plain td, table.violations th, table.violations td, table.matrix th, table.matrix td {
    border: 1px solid var(--border); padding: .45rem .6rem; text-align: left; vertical-align: top;
  }
  table th { background: var(--card-bg); font-weight: 600; font-size: 13px; }
  /* .cov = the two coverage-by-criterion tables only (Check/Item text tables
     must NOT get this narrow right-aligned numeric-column treatment). */
  table.cov td.num, table.cov th:nth-child(2), table.cov th:nth-child(3), table.cov th:nth-child(4) { text-align: right; width: 3rem; }
  table.cov th:first-child, table.cov td:first-child { width: auto; }
  table.cov td:last-child { width: 140px; }
  /* Outstanding/Passed tables are 3 columns (Check/Item/WCAG); explicit
     proportions since content length gives the browser's auto layout no
     useful signal — a long WCAG list otherwise gets squeezed to ~15% width
     and wraps to 5+ lines per row. */
  table.plain:not(.cov) { table-layout: fixed; }
  table.plain:not(.cov) th:nth-child(1), table.plain:not(.cov) td:nth-child(1) { width: 52%; }
  table.plain:not(.cov) th:nth-child(2), table.plain:not(.cov) td:nth-child(2) { width: 16%; }
  table.plain:not(.cov) th:nth-child(3), table.plain:not(.cov) td:nth-child(3) { width: 32%; font-size: 12.5px; }
  table.violations { margin-top: .75rem; font-size: 13px; }

  .table-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
  table.matrix { margin: 0; font-size: 13px; }
  table.matrix th:first-child, table.matrix td:first-child { position: sticky; left: 0; background: var(--card-bg); text-align: left; }
  table.matrix th { white-space: nowrap; }
  table.matrix td { text-align: center; }
  .cell { display: inline-flex; align-items: center; justify-content: center; width: 1.4em; height: 1.4em; border-radius: 5px; font-weight: 700; }
  .cell.pass { background: var(--pass-bg); color: var(--pass); }
  .cell.fail { background: var(--fail-bg); color: var(--fail); }
  .cell.pending { background: var(--pending-bg); color: var(--pending); }
  .cell.na { color: var(--muted); }
  .legend { font-size: 13px; color: var(--muted); margin-top: .5rem; }

  .note { color: var(--muted); font-size: 13.5px; }
  blockquote { border-left: 3px solid var(--pending); margin: .75rem 0; padding: .3rem .9rem; background: var(--pending-bg); border-radius: 0 8px 8px 0; font-size: 13.5px; }

  details summary { cursor: pointer; }
  details[open] summary { margin-bottom: .5rem; }

  .empty { text-align: center; padding: 4rem 1rem; color: var(--muted); }
"""


def main():
    findings = load_findings()
    md = build_markdown(findings)
    MD_OUT.write_text(md, encoding="utf-8")
    HTML_OUT.write_text(build_html(findings), encoding="utf-8")

    failed = sum(1 for f in findings if f["status"] == "fail")
    pending = sum(1 for f in findings if f["status"] == "not_implemented")
    print(f"✔️ ACCESSIBILITY_REPORT.md generated ({len(findings)} findings, "
          f"{failed} failed, {pending} not implemented)")
    print(f"✔️ ACCESSIBILITY_REPORT.html generated")


if __name__ == "__main__":
    main()
