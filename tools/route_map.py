"""Frontend page routes (app/[locale]/**/page.tsx) vs. path fragments appearing in tests/ and pages/.
Usage: python tools/route_map.py ../DataSpaceFrontend"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]) / "app" / "[locale]"
src = "\n".join(p.read_text(errors="ignore") for d in ("tests", "pages", "locators", "utils") for p in pathlib.Path(d).rglob("*.py"))
routes = sorted("/" + re.sub(r"\([^)]*\)/?", "", str(p.parent.relative_to(root))).strip("/") for p in root.rglob("page.tsx"))
miss = []
for r in routes:
    static = [s for s in r.split("/") if s and not s.startswith("[")]
    key = "/".join(static[-2:]) if static else "/"
    if key != "/" and key not in src:
        miss.append(r)
print(f"{len(routes)} routes, {len(routes) - len(miss)} with a path fragment in tests/pages, {len(miss)} without:")
print("\n".join("  " + r for r in miss))
