# Tiny helpers for response-time budget tests. Budgets are generous by default
# (dev answers in ~1s through the proxy) and overridable per environment.

import os
import time

N_REQUESTS = int(os.getenv("PERF_REQUESTS", "20"))


def budget(name, default):
    """Seconds, from env PERF_<NAME> (e.g. PERF_P95_S) or the default."""
    try:
        return float(os.getenv(f"PERF_{name}", default))
    except ValueError:
        return float(default)


def percentile(sorted_values, pct):
    """Nearest-rank percentile of an ascending list."""
    rank = max(1, -(-len(sorted_values) * pct // 100))
    return sorted_values[int(rank) - 1]


def sample(request_fn, n=N_REQUESTS):
    """Time `n` sequential requests; each must return 200. Returns ascending seconds."""
    times = []
    for i in range(n):
        started = time.perf_counter()
        resp = request_fn()
        times.append(time.perf_counter() - started)
        assert resp.status_code == 200, f"request {i + 1}/{n} returned {resp.status_code}"
    return sorted(times)
