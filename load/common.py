# load/common.py
#
# Shared pieces for the CivicDataSpace load tests (DataSpace#268): dev-only
# guard, the stepped ramp, and the automatic stop rules.
#
# Rate limiting stays ON (decision 2026-10-06): the backend allows 5000 GET and
# 1000 non-GET requests per hour per IP, so a single load machine reaches the
# limiter early. 429s are counted separately so the report can show where it
# starts. Once tripped, this machine's IP stays throttled for up to an hour.
#
# Sharded runs (.github/workflows/load-test.yml): LOAD_SHARDS processes on
# different runners each take their share of every step (LOAD_SHARD_INDEX),
# wait for a common LOAD_START_AT (epoch seconds) so the steps line up, and log
# every request to LOAD_RAW_CSV so aggregate.py can compute exact percentiles.

import csv
import os
import time

import gevent
from locust import LoadTestShape, events

FRONTEND = os.getenv("LOAD_FRONTEND", "https://dev.civicdataspace.in")
API = os.getenv("LOAD_API", "https://dev.api.civicdataspace.in")

# Never anything but dev: load on prod is an outage, and prod runs read-only tests only.
assert FRONTEND.startswith("https://dev.") and API.startswith("https://dev."), (FRONTEND, API)

MAX_FAIL_RATIO = float(os.getenv("LOAD_MAX_FAIL_RATIO", "0.05"))
MAX_P95_MS = float(os.getenv("LOAD_MAX_P95_MS", "5000"))
STEPS = [int(n) for n in os.getenv("LOAD_STEPS", "1,5,10,25,50,100").split(",")]
STEP_SECONDS = int(os.getenv("LOAD_STEP_SECONDS", "180"))
STOP_AFTER = int(os.getenv("LOAD_STOP_AFTER", "3"))
SHARDS = int(os.getenv("LOAD_SHARDS", "1"))
SHARD_INDEX = int(os.getenv("LOAD_SHARD_INDEX", "0"))
START_AT = float(os.getenv("LOAD_START_AT", "0"))
RAW_CSV = os.getenv("LOAD_RAW_CSV")


def share(users):
    """This shard's part of a step's total users (the remainder goes to the lowest indexes)."""
    return users // SHARDS + (1 if SHARD_INDEX < users % SHARDS else 0)

rate_limited = {"count": 0, "first_at_users": None}


def check(response, label):
    """Mark a response failed unless 2xx; 429s are tallied apart from other failures."""
    if response.status_code == 429:
        rate_limited["count"] += 1
        if rate_limited["first_at_users"] is None:
            rate_limited["first_at_users"] = _current_users()
            # nginx answers with an HTML page; the Django limiter with an empty body.
            source = "nginx" if b"nginx" in response.content.lower() else "app (Django limiter)"
            print(f"[429] first one at {_current_users()} users on {response.request.method} "
                  f"{response.url.split('?')[0]}: from {source}, Server={response.headers.get('Server')}")
        response.failure("429 rate limited")
    elif not 200 <= response.status_code < 300:
        response.failure(f"HTTP {response.status_code}")
    elif label == "graphql":
        try:
            body = response.json()
        except ValueError:
            response.failure("non-JSON GraphQL response")
            return
        if body.get("errors"):
            response.failure(f"GraphQL error: {body['errors'][0].get('message', '')[:80]}")
        else:
            response.success()
    else:
        response.success()


_runner = {"env": None}


def _current_users():
    env = _runner["env"]
    return env.runner.user_count if env and env.runner else None


class SteppedRamp(LoadTestShape):
    """Hold each user count in LOAD_STEPS for LOAD_STEP_SECONDS (this shard's share), then stop."""

    def tick(self):
        step = int(self.get_run_time() // STEP_SECONDS)
        if step >= len(STEPS):
            return None
        users = share(STEPS[step])
        return users, max(1, users)


_raw = {"file": None, "writer": None, "t0": None}


@events.request.add_listener
def _log_request(request_type, name, response_time, exception, **_):
    if not _raw["writer"]:
        return
    elapsed = time.time() - _raw["t0"]
    step = min(int(elapsed // STEP_SECONDS), len(STEPS) - 1)
    outcome = "ok" if exception is None else ("429" if "429" in str(exception) else "fail")
    _raw["writer"].writerow([f"{time.time():.3f}", STEPS[step], SHARD_INDEX, name, f"{response_time:.1f}", outcome,
                             "" if exception is None else str(exception)[:120]])


@events.test_start.add_listener
def _open_raw(**_):
    _raw["t0"] = time.time()
    if RAW_CSV:
        _raw["file"] = open(RAW_CSV, "w", newline="")
        _raw["writer"] = csv.writer(_raw["file"])
        _raw["writer"].writerow(["ts", "step_users", "shard", "name", "ms", "outcome", "error"])


@events.init.add_listener
def _start_watchdog(environment, **_):
    _runner["env"] = environment
    if environment.runner is None:
        return
    if START_AT:
        wait = START_AT - time.time()
        print(f"[SHARD {SHARD_INDEX}/{SHARDS}] waiting {max(0, wait):.0f}s for the common start")
        time.sleep(max(0, wait))

    def watch():
        # A breach must hold for STOP_AFTER consecutive checks (5s apart): Locust's
        # "current" p95 covers ~10s, so at low request rates one slow call would
        # otherwise stop the whole run (it did, 2026-10-06, on a single 10s request).
        breaches = 0
        while True:
            time.sleep(5)
            stats = environment.stats.total
            if stats.num_requests < 20:
                continue
            p95 = stats.get_current_response_time_percentile(0.95) or 0
            reason = None
            if stats.fail_ratio > MAX_FAIL_RATIO:
                reason = f"fail ratio {stats.fail_ratio:.1%} > {MAX_FAIL_RATIO:.0%}"
            elif p95 > MAX_P95_MS:
                reason = f"current p95 {p95:.0f}ms > {MAX_P95_MS:.0f}ms"
            breaches = breaches + 1 if reason else 0
            if reason and breaches < STOP_AFTER:
                print(f"[WARN] {reason} at {environment.runner.user_count} users ({breaches}/{STOP_AFTER})")
            if reason and breaches >= STOP_AFTER:
                print(f"\n[STOP] {reason} at {environment.runner.user_count} users "
                      f"(429s so far: {rate_limited['count']}, first at {rate_limited['first_at_users']} users)")
                environment.runner.quit()
                return

    gevent.spawn(watch)


@events.quitting.add_listener
def _summary(environment, **_):
    if _raw["file"]:
        _raw["file"].close()
    print(f"[SUMMARY] 429 responses: {rate_limited['count']}; first seen at "
          f"{rate_limited['first_at_users']} concurrent users")
