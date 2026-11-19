# tests/api/load/safety.py
#
# The one place the safety rules for load/stress tests live. Every load or
# stress test calls `guard(target_url)` first and drives traffic only through
# `run_load`, which enforces the rest.
#
#   a. refuses unless RUN_LOAD_TESTS=1
#   b. refuses when the target equals, or resolves to the same address as,
#      production (HOME_URL_PROD, API_BASE_URL_PROD, api.datakeep.civicdays.in)
#   c. concurrency and duration come from env with low defaults and a hard ceiling
#   d. stops at the first 429 or 5xx burst and reports it
#   e. read-only: GET, or anonymous GraphQL queries (a mutation is refused)
#
# Env:  RUN_LOAD_TESTS=1 (required)
#       LOAD_CONCURRENCY  default 5,  hard ceiling 50
#       LOAD_DURATION_S   default 10, hard ceiling 60
#       LOAD_MAX_5XX      5xx responses that count as a burst, default 3

import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import pytest
import requests

DEFAULT_CONCURRENCY, MAX_CONCURRENCY = 5, 50
DEFAULT_DURATION_S, MAX_DURATION_S = 10, 60
KNOWN_PROD_URLS = ("https://api.datakeep.civicdays.in",)
REQUEST_TIMEOUT = 30


def _host(url):
    return (urlparse(url if "//" in url else f"//{url}").hostname or "").lower()


def _addresses(host):
    try:
        return {ai[4][0] for ai in socket.getaddrinfo(host, None)}
    except OSError:
        return set()


def prod_hosts():
    urls = [os.getenv("HOME_URL_PROD"), os.getenv("API_BASE_URL_PROD"), *KNOWN_PROD_URLS]
    return {_host(u) for u in urls if u}


def is_prod(url):
    """True if `url` is a production host, or resolves to a production address."""
    host = _host(url)
    prods = prod_hosts()
    if host in prods:
        return True
    prod_addrs = set().union(*(_addresses(h) for h in prods)) if prods else set()
    return bool(_addresses(host) & prod_addrs)


def _bounded_env(name, default, ceiling):
    try:
        value = int(os.getenv(name, default))
    except ValueError:
        value = default
    return max(1, min(value, ceiling))


def limits():
    """(concurrency, duration_s), clamped to the hard ceilings."""
    return (
        _bounded_env("LOAD_CONCURRENCY", DEFAULT_CONCURRENCY, MAX_CONCURRENCY),
        _bounded_env("LOAD_DURATION_S", DEFAULT_DURATION_S, MAX_DURATION_S),
    )


def guard(target_url):
    """Skip unless opted in; fail loudly if the target is production."""
    if os.getenv("RUN_LOAD_TESTS") != "1":
        pytest.skip("load/stress tests are opt-in: set RUN_LOAD_TESTS=1")
    assert not is_prod(target_url), (
        f"refusing to run load/stress traffic against {_host(target_url)}: "
        "it is, or resolves to, a production host"
    )


def get(url):
    return requests.get(url, timeout=REQUEST_TIMEOUT)


def graphql_query(endpoint, query):
    """Anonymous GraphQL query. Mutations and subscriptions are refused."""
    head = query.lstrip().split("{", 1)[0].split("(", 1)[0].strip().split(" ")[0]
    assert head not in ("mutation", "subscription"), "load tests are read-only"
    return requests.post(endpoint, json={"query": query}, timeout=REQUEST_TIMEOUT)


def run_load(request_fn, concurrency, duration_s):
    """Call `request_fn()` (returns a Response) from `concurrency` threads for
    `duration_s`, stopping everyone at the first 429 or burst of 5xx.

    Returns a dict: total, ok, statuses (code -> count), aborted (reason or None),
    latencies (sorted seconds), errors (transport failures).
    """
    max_5xx = _bounded_env("LOAD_MAX_5XX", 3, 1000)
    stop = threading.Event()
    lock = threading.Lock()
    result = {"statuses": {}, "latencies": [], "errors": 0, "aborted": None}
    deadline = time.monotonic() + duration_s

    def worker():
        while not stop.is_set() and time.monotonic() < deadline:
            started = time.monotonic()
            try:
                status = request_fn().status_code
            except requests.RequestException:
                with lock:
                    result["errors"] += 1
                continue
            elapsed = time.monotonic() - started
            with lock:
                result["statuses"][status] = result["statuses"].get(status, 0) + 1
                result["latencies"].append(elapsed)
                five = sum(n for s, n in result["statuses"].items() if s >= 500)
                if status == 429 and not result["aborted"]:
                    result["aborted"] = "429 rate limited"
                elif five >= max_5xx and not result["aborted"]:
                    result["aborted"] = f"{five} responses with 5xx"
                if result["aborted"]:
                    stop.set()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for _ in range(concurrency):
            pool.submit(worker)

    result["latencies"].sort()
    result["total"] = len(result["latencies"])
    result["ok"] = sum(n for s, n in result["statuses"].items() if s < 400)
    return result
