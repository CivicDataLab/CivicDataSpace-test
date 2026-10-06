# load/locustfile_provider.py
#
# Providers creating datasets on dev: addDataset -> updateDataset (title,
# description) -> upload a small CSV (createFileResources) -> deleteDataset.
# Nothing is published, so nothing reaches search or public listings.
#
#   locust -f load/locustfile_provider.py --headless --csv load/out/provider
#
# Logs in once per test account (TEST_EMAIL_1..3 from the repo's .env) and
# reuses the tokens: the Keycloak realm is shared with prod, so it must never
# take load. Datasets left behind by a stop mid-iteration are deleted when the
# run ends.

import json
import os
import time
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from locust import HttpUser, between, events, task

from common import API, SteppedRamp, check  # noqa: F401  (SteppedRamp is picked up by Locust)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CSV = b"state,year,value\nAssam,2024,1\nBihar,2024,2\n"
tokens = []
created = {}  # dataset id -> Session of the account that created it


class Session:
    """One account's Django tokens. Access tokens last 5 minutes on dev, so refresh
    every 4 through /api/auth/token/refresh/ (exempt from the limiter, no Keycloak)."""

    def __init__(self, access, refresh):
        self.access, self.refresh_token, self.issued = access, refresh, time.time()

    def token(self):
        if time.time() - self.issued > 240:
            r = requests.post(f"{API}/api/auth/token/refresh/", json={"refresh": self.refresh_token}, timeout=60)
            if r.status_code == 200 and r.json().get("access"):
                self.access, self.issued = r.json()["access"], time.time()
        return self.access


def _login(n):
    kc = os.environ["KEYCLOAK_URL"].rstrip("/")
    payload = {
        "grant_type": "password", "client_id": os.environ["KEYCLOAK_CLIENT_ID"],
        "username": os.environ[f"TEST_EMAIL_{n}"], "password": os.environ[f"TEST_PASSWORD_{n}"],
    }
    if os.getenv("KEYCLOAK_CLIENT_SECRET"):
        payload["client_secret"] = os.environ["KEYCLOAK_CLIENT_SECRET"]
    kc_token = requests.post(f"{kc}/realms/{os.environ['KEYCLOAK_REALM']}/protocol/openid-connect/token",
                             data=payload, timeout=30).json()["access_token"]
    tokens = requests.post(f"{API}/api/auth/keycloak/login/", json={"token": kc_token}, timeout=90).json()
    return Session(tokens["access"], tokens["refresh"])


@events.test_start.add_listener
def _tokens(**_):
    # LOAD_ACCOUNTS (e.g. "2") limits the logins, so 20 shards cost ~20 Keycloak logins, not 60.
    accounts = [int(n) for n in os.getenv("LOAD_ACCOUNTS", "1,2,3").split(",")]
    tokens.extend(_login(n) for n in accounts if os.getenv(f"TEST_EMAIL_{n}"))
    assert tokens, "no TEST_EMAIL_<n> credentials in .env"


@events.test_stop.add_listener
def _cleanup(**_):
    # Individual datasets can only be deleted by their own account. Rate-limited
    # (429) deletes are left in `created` and retried here.
    gone = []
    for dataset_id, token in list(created.items()):
        r = requests.post(f"{API}/api/graphql", timeout=60, headers={"Authorization": f"Bearer {token.token()}"},
                          json={"query": "mutation($id: UUID!){ deleteDataset(datasetId: $id) }", "variables": {"id": dataset_id}})
        if r.status_code == 200 and (r.json().get("data") or {}).get("deleteDataset"):
            gone.append(created.pop(dataset_id))
    print(f"[CLEANUP] deleted {len(gone)} leftover dataset(s); {len(created)} still left: {list(created)}")


class Provider(HttpUser):
    host = API
    wait_time = between(3, 8)

    def on_start(self):
        self.session = tokens[id(self) % len(tokens)]

    def _gql(self, name, query, variables, refused=None):
        """POST a mutation; `refused(body)` returns an error message when the payload says no."""
        with self.client.post("/api/graphql", json={"query": query, "variables": variables},
                              headers=self._headers(), name=f"gql {name}", catch_response=True) as r:
            check(r, "graphql")
            body = r.json() if r.status_code == 200 else {}
            message = refused(body) if refused and body.get("data") else None
            if message:
                r.failure(message)
            return body

    def _headers(self):
        return {"Authorization": f"Bearer {self.session.token()}"}

    @task
    def create_dataset(self):
        # A 200 with success:false (e.g. "User is not authenticated") is a failure, not a pass.
        body = self._gql("addDataset",
                         "mutation{ addDataset(createInput: {datasetType: DATA}){ success errors { nonFieldErrors } data { id } } }", {},
                         refused=lambda b: None if (b["data"]["addDataset"] or {}).get("success")
                         else str(((b["data"]["addDataset"] or {}).get("errors") or {}).get("nonFieldErrors") or "addDataset success=false"))
        dataset_id = ((body.get("data") or {}).get("addDataset") or {}).get("data", {}).get("id")
        if not dataset_id:
            return
        created[dataset_id] = self.session
        self._gql("updateDataset",
                  "mutation($i: UpdateDatasetInput!){ updateDataset(updateDatasetInput: $i){"
                  " ... on TypeDataset { id } ... on OperationInfo { messages { message } } } }",
                  {"i": {"dataset": dataset_id, "title": f"loadtest {uuid.uuid4().hex[:8]}",
                         "description": "Load test dataset, deleted automatically."}},
                  refused=lambda b: "; ".join(m["message"] for m in b["data"]["updateDataset"].get("messages") or []))
        operations = {"query": "mutation($i: CreateFileResourceInput!){ createFileResources(fileResourceInput: $i){ id } }",
                      "variables": {"i": {"dataset": dataset_id, "files": [None]}}}
        with self.client.post("/api/graphql", name="gql createFileResources (upload)", catch_response=True,
                              headers=self._headers(),
                              data={"operations": json.dumps(operations), "map": json.dumps({"0": ["variables.i.files.0"]})},
                              files={"0": ("load.csv", CSV, "text/csv")}) as r:
            check(r, "graphql")
        body = self._gql("deleteDataset", "mutation($id: UUID!){ deleteDataset(datasetId: $id) }", {"id": dataset_id},
                         refused=lambda b: None if b["data"].get("deleteDataset") else "deleteDataset returned false")
        if (body.get("data") or {}).get("deleteDataset"):
            created.pop(dataset_id, None)
