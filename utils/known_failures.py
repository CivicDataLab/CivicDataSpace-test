"""Known-failures gate.

A failed test listed in known_failures.txt still fails and is reported, but does not
fail the run. Any failure that is not listed does. Enabled by KNOWN_FAILURES=on (set in
run-smoke.yml for every suite except readonly, so prod keeps its strict gate).
"""
import os
import re
from pathlib import Path

import pytest

LIST = Path(os.getenv("KNOWN_FAILURES_FILE") or Path(__file__).resolve().parent.parent / "known_failures.txt")


def _entries():
    out = {}
    for line in LIST.read_text().splitlines():
        entry, _, why = line.partition("#")
        if entry.strip():
            out[entry.strip()] = why.strip()
    return out


def _covers(entry, nid):
    return nid == entry or (nid.startswith(entry) and nid[len(entry)] in "[:")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if os.getenv("KNOWN_FAILURES") != "on" or hasattr(session.config, "workerinput") or exitstatus != 1:
        return
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    nid = lambda r: r.nodeid.split("@")[0]
    bad = sorted({nid(r) for k in ("failed", "error") for r in tr.stats.get(k, [])})
    known = _entries()
    unknown = [b for b in bad if not any(_covers(e, b) for e in known)]
    hit = sorted({e for e in known for b in bad if _covers(e, b)})
    ran = {nid(r) for r in tr.stats.get("passed", [])}
    fixed = sorted(e for e in known if e not in hit and any(_covers(e, p) for p in ran))

    lines = [f"Known failures (do not block the deploy): {len(hit)} entries"]
    lines += [f"  {e}  # {known[e]}" for e in hit]
    if fixed:
        lines += ["Known failures now PASSING, delete from known_failures.txt:"] + [f"  {e}" for e in fixed]
    if unknown:
        lines += [f"NEW failures not in known_failures.txt ({len(unknown)}), run stays red:"] + [f"  {b}" for b in unknown]
    tr.write_sep("=", "known failures")
    tr.write_line("\n".join(lines))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("### Known failures\n```\n" + "\n".join(lines) + "\n```\n")
    if hit or fixed:
        print(f"::warning::{len(hit)} known failures not blocking; {len(fixed)} now passing and can be removed from known_failures.txt")
    if not unknown:
        session.exitstatus = 0
