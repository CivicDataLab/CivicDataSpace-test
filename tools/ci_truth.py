"""Which collected tests does no CI lane ever run? Lanes mirror run-smoke.yml."""
import subprocess
import sys

LANES = {  # (path, marker) per job/suite; push/PR = smoke, dispatch/call = smoke or functional
    "consumer push": ("tests/consumer", "smoke"),
    "consumer dispatch": ("tests/consumer", "smoke or functional"),
    "api push": ("tests/api/smoke", "smoke"),
    "api dispatch": ("tests/api/smoke", "smoke or functional"),
    "provider push": ("tests/provider/smoke", "smoke"),
    "provider dispatch": ("tests/provider/smoke", "smoke or functional"),
    "api-matrix": ("tests/api/functional", "functional"),
    "suite full": ("tests", "smoke or functional or regression"),
    "keycloak": ("tests/consumer/smoke/test_con_auth_pages.py tests/api/smoke/test_api_007_keycloak_migration.py", ""),
}


def collect(path, marker):
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *path.split()]
    if marker:
        cmd += ["-m", marker]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return {l for l in out.splitlines() if "::" in l}


def main(lanes):
    everything = collect("tests", "")
    ran = set()
    for name, (p, m) in lanes.items():
        if name == "suite full":
            continue  # manual suite, reported separately
        ids = collect(p, m)
        ran |= ids
        print(f"{name:20} {len(ids):4}")
    full = collect(*lanes["suite full"])
    print(f"{'suite full (manual)':20} {len(full):4}\nall collected        {len(everything):4}")
    print(f"\nNEVER in a push/dispatch/keycloak lane: {len(everything - ran)}")
    print(f"NEVER in any lane incl. 'full':          {len(everything - ran - full)}")
    from collections import Counter
    for f, n in sorted(Counter(t.split("::")[0] for t in everything - ran - full).items()):
        print(f"   {n:3} {f}")


if __name__ == "__main__":
    main(LANES)
