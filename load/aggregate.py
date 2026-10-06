# load/aggregate.py
#
# Merge the raw per-request logs of a sharded load run (common.py LOAD_RAW_CSV)
# into one Markdown report: per step, total requests/s, p50/p95/p99 of
# successful requests (429s answer instantly and would flatter the numbers),
# 429s and other failures; the slowest calls at the highest clean step; and any
# runner IPs that more than one shard shared.
#
#   python load/aggregate.py <dir with raw_*.csv and ip_*.txt> > report.md

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def pct(values, q):
    if not values:
        return None
    return statistics.quantiles(values, n=100, method="inclusive")[q - 1] if len(values) > 1 else values[0]


def ms(v):
    return "—" if v is None else (f"{v / 1000:.1f} s" if v >= 1000 else f"{v:.0f} ms")


def main(folder):
    rows = []
    for f in sorted(Path(folder).glob("**/raw_*.csv")):
        rows += list(csv.DictReader(f.open()))
    if not rows:
        print("No requests recorded.")
        return

    steps = defaultdict(list)
    for r in rows:
        steps[int(r["step_users"])].append(r)

    print("| Users | Requests | Req/s | p50 | p95 | p99 | 429s | Other failures |")
    print("|---|---|---|---|---|---|---|---|")
    clean = None
    for users in sorted(steps):
        rs = steps[users]
        ts = [float(r["ts"]) for r in rs]
        span = max(max(ts) - min(ts), 1)
        ok = sorted(float(r["ms"]) for r in rs if r["outcome"] == "ok")
        n429 = sum(r["outcome"] == "429" for r in rs)
        nfail = sum(r["outcome"] == "fail" for r in rs)
        if n429 == 0 and nfail <= 0.05 * len(rs):
            clean = users
        print(f"| {users} | {len(rs)} | {len(rs) / span:.1f} | {ms(pct(ok, 50))} | {ms(pct(ok, 95))} | "
              f"{ms(pct(ok, 99))} | {n429} | {nfail} |")

    if clean is not None:
        print(f"\n**Slowest calls at {clean} users** (highest step without 429s):\n")
        by_name = defaultdict(list)
        for r in steps[clean]:
            if r["outcome"] == "ok":
                by_name[r["name"]].append(float(r["ms"]))
        print("| Call | Requests | p50 | p95 | max |")
        print("|---|---|---|---|---|")
        for name, v in sorted(by_name.items(), key=lambda kv: -(pct(sorted(kv[1]), 95) or 0))[:8]:
            v.sort()
            print(f"| {name} | {len(v)} | {ms(pct(v, 50))} | {ms(pct(v, 95))} | {ms(v[-1])} |")

    errors = defaultdict(int)
    for r in rows:
        if r["outcome"] == "fail":
            errors[(r["name"], r["error"])] += 1
    if errors:
        print("\n**Failures other than 429:**\n")
        for (name, err), n in sorted(errors.items(), key=lambda kv: -kv[1])[:10]:
            print(f"- {n}× `{name}`: {err}")

    ips = defaultdict(list)
    for f in sorted(Path(folder).glob("**/ip_*.txt")):
        ips[f.read_text().strip()].append(f.stem.removeprefix("ip_"))
    shared = {ip: s for ip, s in ips.items() if len(s) > 1}
    print(f"\nRunner IPs: {len(ips)} distinct across {sum(len(s) for s in ips.values())} shards"
          + (f"; shared: {shared}" if shared else "; none shared."))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
