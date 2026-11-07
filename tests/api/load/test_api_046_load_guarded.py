# tests/api/load/test_api_046_load_guarded.py
#
# Opt-in load and stress checks against the public read endpoints of the dev API.
# Never runs on push/PR or the default dispatch: markers are `load`/`stress`
# only, and the files live outside tests/api/smoke. Run locally with
#   RUN_LOAD_TESTS=1 pytest tests/api/load -m "load or stress"
#
# These are indicators for one client against dev, not capacity numbers.

import pytest

from tests.api.load import safety

pytestmark = pytest.mark.api

SECTORS = "{ sectors { name } }"


@pytest.mark.load
def test_safety_guard_rejects_prod_and_caps_limits(monkeypatch):
    """The guard must recognise prod hosts and clamp env-requested limits.

    Pure logic, no traffic, so it runs without RUN_LOAD_TESTS: if this breaks,
    the opt-in tests below must not be trusted.
    """
    assert safety.is_prod("https://api.datakeep.civicdays.in/api/graphql")
    monkeypatch.setenv("HOME_URL_PROD", "https://civicdataspace.in")
    assert safety.is_prod("https://civicdataspace.in/")
    assert not safety.is_prod("https://example.invalid")

    monkeypatch.setenv("LOAD_CONCURRENCY", "9999")
    monkeypatch.setenv("LOAD_DURATION_S", "9999")
    assert safety.limits() == (safety.MAX_CONCURRENCY, safety.MAX_DURATION_S)
    monkeypatch.delenv("LOAD_CONCURRENCY")
    monkeypatch.delenv("LOAD_DURATION_S")
    assert safety.limits() == (safety.DEFAULT_CONCURRENCY, safety.DEFAULT_DURATION_S)

    with pytest.raises(AssertionError):
        safety.graphql_query("https://example.invalid/api/graphql", "mutation { x }")


@pytest.mark.load
def test_safety_run_load_aborts_on_429():
    """run_load must stop on the first 429 instead of continuing to the deadline."""
    class Resp:
        status_code = 429

    out = safety.run_load(lambda: Resp(), concurrency=3, duration_s=30)
    assert out["aborted"] == "429 rate limited"
    assert out["total"] <= 3, f"kept sending after a 429: {out}"


@pytest.mark.load
def test_graphql_public_query_holds_under_light_load(api_base_url):
    """Sustained anonymous GraphQL reads at the low default must all succeed."""
    safety.guard(api_base_url)
    concurrency, duration = safety.limits()
    out = safety.run_load(
        lambda: safety.graphql_query(f"{api_base_url}/api/graphql", SECTORS),
        concurrency, duration,
    )
    print(f"load graphql c={concurrency} d={duration}s -> {out['total']} req, statuses={out['statuses']}")
    assert out["aborted"] is None, f"load stopped early: {out['aborted']} {out['statuses']}"
    assert out["errors"] == 0, f"{out['errors']} transport errors under load"
    assert out["ok"] == out["total"] > 0, f"non-2xx/3xx responses under load: {out['statuses']}"


@pytest.mark.stress
def test_search_endpoint_survives_stepped_ramp(api_base_url):
    """Ramp concurrency 1 -> cap in short steps; the endpoint must never 5xx or 429.

    The ceiling is the same capped LOAD_CONCURRENCY, so 'stress' here means
    stepping up to the cap, never beyond it.
    """
    safety.guard(api_base_url)
    cap, duration = safety.limits()
    steps = sorted({1, max(1, cap // 2), cap})
    per_step = max(2, duration // len(steps))
    for c in steps:
        out = safety.run_load(lambda: safety.get(f"{api_base_url}/api/search/dataset/"), c, per_step)
        print(f"stress step c={c} d={per_step}s -> {out['total']} req, statuses={out['statuses']}")
        assert out["aborted"] is None, f"stopped at concurrency {c}: {out['aborted']} {out['statuses']}"
        assert out["errors"] == 0 and out["ok"] == out["total"] > 0, f"concurrency {c}: {out}"
