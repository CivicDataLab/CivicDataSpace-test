# tests/api/performance/test_api_045_response_time_budgets.py
#
# Response-time budgets for key anonymous endpoints: N sequential requests,
# p50 and p95 compared to a budget. Budgets are deliberately generous so
# network jitter does not fail the run; they catch order-of-magnitude
# regressions (an N+1 query, a lost index, a cache that stopped working).
# Overrides: PERF_P50_S, PERF_P95_S, PERF_REQUESTS. Dev-only indicators.

import pytest

from tests.api.performance.conftest import budget, percentile, sample

pytestmark = [pytest.mark.api, pytest.mark.performance]

P50_S = budget("P50_S", 3.0)
P95_S = budget("P95_S", 8.0)


def _check(name, times):
    p50, p95 = percentile(times, 50), percentile(times, 95)
    print(f"{name}: n={len(times)} p50={p50:.3f}s p95={p95:.3f}s max={times[-1]:.3f}s")
    assert p50 <= P50_S, f"{name} p50 {p50:.2f}s over budget {P50_S}s"
    assert p95 <= P95_S, f"{name} p95 {p95:.2f}s over budget {P95_S}s"


@pytest.mark.parametrize("path", [
    "/health/",
    "/api/search/dataset/",
    "/api/search/usecase/",
], ids=["health", "search_dataset", "search_usecase"])
def test_rest_endpoint_response_time(anon_api_client, path):
    # session.get, not APIClient.get: the client retries gateway errors with a
    # sleep, which would hide or inflate exactly what is being measured.
    url = f"{anon_api_client.base_url}{path}"
    _check(path, sample(lambda: anon_api_client.session.get(url, timeout=30)))


@pytest.mark.parametrize("query", [
    "{ sectors { name } }",
    "{ useCases { id title } }",
], ids=["sectors", "use_cases"])
def test_graphql_query_response_time(anon_api_client, query):
    url = f"{anon_api_client.base_url}/api/graphql"
    _check(query, sample(lambda: anon_api_client.session.post(url, json={"query": query}, timeout=30)))
