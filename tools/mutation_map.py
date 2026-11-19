"""Live-introspect GraphQL mutations (dev, read-only) and list which appear in tests/.
Usage: API_BASE_URL=... python tools/mutation_map.py"""
import json
import os
import pathlib
import re
import urllib.request

url = os.environ["API_BASE_URL"].rstrip("/") + "/api/graphql"
q = '{__schema{mutationType{fields{name}} queryType{fields{name}}}}'
req = urllib.request.Request(url, json.dumps({"query": q}).encode(), {"Content-Type": "application/json"})
s = json.load(urllib.request.urlopen(req, timeout=30))["data"]["__schema"]
src = "\n".join(p.read_text(errors="ignore") for p in pathlib.Path("tests").rglob("*.py")) + "\n".join(
    p.read_text(errors="ignore") for p in pathlib.Path("pages").rglob("*.py"))
for kind in ("mutationType", "queryType"):
    names = sorted(f["name"] for f in s[kind]["fields"])
    hit = {n: len(re.findall(rf"\b{re.escape(n)}\b", src)) for n in names}
    miss = [n for n, c in hit.items() if not c]
    print(f"\n{kind}: {len(names)} total, {len(names) - len(miss)} referenced in tests, {len(miss)} not")
    print("  NOT referenced:", ", ".join(miss))
