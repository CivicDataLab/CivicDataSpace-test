# load/locustfile_consumer.py
#
# Anonymous visitors browsing CivicDataSpace on dev. Each task loads a page's
# HTML from the frontend (server-side rendering) and then replays the backend
# calls a real browser makes for that page, captured from dev on 2026-10-06
# (consumer_pages.json). Weights roughly follow how people browse.
#
#   locust -f load/locustfile_consumer.py --headless --csv load/out/consumer
#
# Ramp and stop rules: see common.py (LOAD_STEPS, LOAD_STEP_SECONDS, ...).

import json
import random
from pathlib import Path

from locust import HttpUser, between, task

from common import API, FRONTEND, SteppedRamp, check  # noqa: F401  (SteppedRamp is picked up by Locust)

DATA = json.loads((Path(__file__).parent / "consumer_pages.json").read_text())
PAGES, DATASET_IDS = DATA["pages"], DATA["dataset_ids"]


class Visitor(HttpUser):
    host = FRONTEND
    wait_time = between(2, 6)  # reading time between page views

    def _view(self, name):
        page = PAGES[name]
        dataset_id = random.choice(DATASET_IDS)
        path = page["page"].replace("{dataset_id}", dataset_id)
        with self.client.get(path, name=f"page {name}", catch_response=True) as r:
            check(r, "page")
        for call in page["calls"]:
            if call["method"] == "GET":
                with self.client.get(API + call["path"].replace("{dataset_id}", dataset_id),
                                     name=f"GET {call['path'].split('?')[0]}", catch_response=True) as r:
                    check(r, "get")
            else:
                body = json.loads(json.dumps(call["body"]).replace("{dataset_id}", dataset_id))
                op = body.get("operationName") or f"{name} query"
                with self.client.post(API + "/api/graphql", json=body, name=f"gql {op}", catch_response=True) as r:
                    check(r, "graphql")

    @task(3)
    def home(self):
        self._view("home")

    @task(3)
    def datasets(self):
        self._view("datasets")

    @task(4)
    def dataset_detail(self):
        self._view("dataset")

    @task(2)
    def usecases(self):
        self._view("usecases")

    @task(2)
    def usecase_detail(self):
        self._view("usecase")

    @task(1)
    def publishers(self):
        self._view("publishers")
