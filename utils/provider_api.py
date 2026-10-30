# utils/provider_api.py
#
# API access for the provider UI tests, used to make them leave dev as they found it.
#
# The provider flows create real records (datasets, use cases, collaboratives,
# AI models, charts, publications) on the shared dev backend. The browser cannot
# be relied on to remove them: a failed assertion stops the test before any UI
# "Delete" step. So every provider test that creates something registers a
# `Cleanup` (the `cleanup` fixture in tests/provider/conftest.py) and the records
# are deleted through the same GraphQL mutations the dashboard's row Delete uses,
# in a finalizer that runs on failure too.
#
# Two ways to register a record:
#   cleanup.watch(kind, org=None)   snapshot the account's listing now; whatever is
#                                   new at teardown was created by this test and is
#                                   deleted. For records the browser creates and the
#                                   test does not know the id of.
#   cleanup.track(kind, id, org)    delete one known record (created via the API).
#
# A deletion that fails, or a record that is still listed afterwards, raises: a
# test that cannot clean up after itself must not look green.

from __future__ import annotations

import base64
import json
import os
import time


from tests.api import publications
from tests.api.client import GraphQLClient
from tests.api.conftest import _exchange_for_django_token, _get_keycloak_token

# kind -> (listing field, selection, delete mutation, delete variable type).
# Charts are special-cased: the listing is a union of two types with two deletes.
KINDS = {
    "dataset": ("datasetsTable", "id", "deleteDataset(datasetId: $id)", "UUID!"),
    "usecase": ("useCasesTable", "id", "deleteUseCase(useCaseId: $id)", "String!"),
    "collaborative": ("collaborativesTable", "id", "deleteCollaborative(collaborativeId: $id)", "String!"),
    "aimodel": ("aiModelsTable", "id", "deleteAiModel(modelId: $id) { success }", "Int!"),
    "publication": ("publicationsTable", "id", "deletePublication(publicationId: $id) { success }", "UUID!"),
}
CHART_DELETE = {
    "TypeResourceChart": ("deleteResourceChart(chartId: $id)", "UUID!"),
    "TypeResourceChartImage": ("deleteResourceChartImage(resourceChartImageId: $id)", "UUID!"),
}
# Dependants first: a dataset can be referenced by charts and use cases.
ORDER = ["chart", "publication", "collaborative", "usecase", "aimodel", "dataset"]
PAGE = 100  # the API rejects a larger limit


class ProviderAPI:
    """Authenticated GraphQL access as the account this worker logs in with.

    The backend's access token lives five minutes, and an expired token is not
    refused: the API answers as an anonymous caller, so a listing silently turns
    into "every published record" and a cleanup finds none of the drafts it made.
    The token is therefore renewed before it runs out.
    """

    RENEW_BEFORE_EXPIRY = 60  # seconds

    def __init__(self, email: str, password: str):
        self._credentials = (email, password)
        self._base = os.environ["API_BASE_URL"].rstrip("/")
        self._slugs: dict[str, str] = {}
        self._expires = 0.0
        self.client = GraphQLClient(self._base)
        self._login()

    def _login(self):
        env = os.environ
        email, password = self._credentials
        kc_token = _get_keycloak_token(
            env["KEYCLOAK_URL"], env["KEYCLOAK_REALM"], env["KEYCLOAK_CLIENT_ID"],
            email, password, client_secret=env.get("KEYCLOAK_CLIENT_SECRET"),
        )
        token = _exchange_for_django_token(self._base, kc_token).json()["access"]
        self.client.session.headers["Authorization"] = f"Bearer {token}"
        payload = token.split(".")[1]
        self._expires = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["exp"]

    def gql(self, query, variables=None, org=None):
        """Run a query and return the whole body. `org` is an organization slug."""
        if time.time() > self._expires - self.RENEW_BEFORE_EXPIRY:
            self._login()
        return publications.gql(self.client, query, variables, org)

    def org_slug(self, org_name: str) -> str:
        if org_name not in self._slugs:
            self._slugs[org_name] = publications.org_slug(self.client, org_name)
        return self._slugs[org_name]

    def _owner(self, org_name):
        return self.org_slug(org_name) if org_name else None

    # -- listing --------------------------------------------------------------

    def listing(self, kind, org_name=None, filters=None):
        """Return the dashboard listing for `kind` as a list of {id, title/name, status, ...}.

        Mirrors what the provider table shows: the individual's own records, or
        the organization's when `org_name` is given.
        """
        field = "chartsTable" if kind == "chart" else KINDS[kind][0]
        if kind == "chart":
            sel = ("__typename ... on TypeResourceChart { id name status } "
                   "... on TypeResourceChartImage { id name status }")
        else:
            sel = "id status " + {"aimodel": "displayName", "publication": "title"}.get(kind, "title")
        rows, offset = [], 0
        while True:
            body = self.gql(
                "query($f: [FilterSpec!], $o: Int){ %s(limit: %d, offset: $o, filters: $f){ totalItemsCount "
                "statusCounts { status count } data { %s } } }" % (field, PAGE, sel),
                {"f": filters, "o": offset}, self._owner(org_name),
            )
            assert "errors" not in body, f"{field} listing failed: {body['errors']}"
            table = body["data"][field]
            rows += table["data"]
            offset += PAGE
            if offset >= table["totalItemsCount"] or not table["data"]:
                return {**table, "data": rows}

    def ids(self, kind, org_name=None):
        return {str(row["id"]) for row in self.listing(kind, org_name)["data"]}

    def names(self, kind, org_name=None):
        """The titles of the listed records (display names for AI models, names for charts)."""
        return [r.get("title") or r.get("displayName") or r.get("name") for r in self.listing(kind, org_name)["data"]]

    def counts(self, org_name=None):
        """{kind: totalItemsCount} for every kind; used to prove a run left no residue."""
        return {kind: self.listing(kind, org_name)["totalItemsCount"] for kind in ORDER}

    # -- creating -------------------------------------------------------------

    def create_draft(self, kind, title, org_name=None):
        """Create a draft called `title` through the API and return its id.

        Mirrors what the dashboard's Create button does (an empty record), plus
        the rename, so tests get a row they can find by name.
        """
        org = self._owner(org_name)
        if kind == "dataset":
            made = self._mutate(
                "mutation{ addDataset(createInput:{datasetType: DATA}){ success data { id } } }", org)
            record_id = made["addDataset"]["data"]["id"]
            self._mutate(
                "mutation($i: UpdateDatasetInput!){ updateDataset(updateDatasetInput:$i){ __typename } }",
                org, {"i": {"dataset": record_id, "title": title}})
        elif kind in ("usecase", "collaborative"):
            add, update = ("addUseCase", "updateUseCase") if kind == "usecase" else ("addCollaborative", "updateCollaborative")
            made = self._mutate("mutation{ %s { __typename ... on Type%s { id } } }" % (
                add, "UseCase" if kind == "usecase" else "Collaborative"), org)
            record_id = made[add]["id"]
            self._mutate(
                "mutation($i: %sInputPartial!){ %s(data:$i){ id } }" % (
                    "UseCase" if kind == "usecase" else "Collaborative", update),
                org, {"i": {"id": record_id, "title": title}})
        elif kind == "aimodel":
            made = self._mutate(
                "mutation($i: CreateAIModelInput!){ createAiModel(input:$i){ success data { id } } }", org,
                {"i": {"name": title.lower().replace(" ", "-"), "displayName": title,
                       "modelType": "TEXT_GENERATION", "provider": "CUSTOM"}})
            record_id = made["createAiModel"]["data"]["id"]
        else:
            raise ValueError(f"cannot create a {kind} draft through the API")
        return str(record_id)

    def _mutate(self, query, org=None, variables=None):
        body = self.gql(query, variables, org)
        assert "errors" not in body, f"{query[:60]}...: {body['errors']}"
        data = body["data"]
        for payload in data.values():
            if isinstance(payload, dict) and payload.get("success") is False:
                raise AssertionError(f"{query[:60]}... refused: {payload}")
        return data

    # -- deleting -------------------------------------------------------------

    def delete(self, kind, record_id, org_name=None, typename=None):
        """Delete one record; returns an error string, or None when it is gone."""
        if kind == "chart":
            mutation, var_type = CHART_DELETE[typename or "TypeResourceChart"]
        else:
            _, _, mutation, var_type = KINDS[kind]
        value = int(record_id) if kind == "aimodel" else str(record_id)
        body = self.gql("mutation($id: %s){ %s }" % (var_type, mutation), {"id": value}, self._owner(org_name))
        if "errors" in body:
            return f"{kind} {record_id}: {body['errors'][0]['message']}"
        result = next(iter(body["data"].values()))
        if isinstance(result, dict):
            result = result.get("success")
        if not result:
            return f"{kind} {record_id}: delete returned {result!r}"
        return None


class Cleanup:
    """Deletes what a test created. See the module docstring."""

    def __init__(self, api: ProviderAPI):
        self.api = api
        self._watched: list[tuple[str, str | None, set[str]]] = []
        self._tracked: list[tuple[str, str, str | None]] = []
        self.deleted: list[str] = []

    def watch(self, kind, org=None):
        """Remember today's records of `kind`; anything new by teardown is deleted."""
        self._watched.append((kind, org, self.api.ids(kind, org)))

    def track(self, kind, record_id, org=None):
        """Delete this one record at teardown, unless the test already did."""
        self._tracked.append((kind, str(record_id), org))

    def run(self):
        failures = []
        todo = list(self._tracked)
        for kind, org, before in self._watched:
            for row in self.api.listing(kind, org)["data"]:
                if str(row["id"]) not in before:
                    todo.append((kind, str(row["id"]), org, row.get("__typename")))
        todo = [t if len(t) == 4 else (*t, None) for t in todo]
        seen = set()
        for kind, record_id, org, typename in sorted(todo, key=lambda t: ORDER.index(t[0])):
            if (kind, record_id) in seen:
                continue
            seen.add((kind, record_id))
            error = self.api.delete(kind, record_id, org, typename)
            # A tracked record the test already deleted itself (through the UI, say)
            # makes the mutation fail; that is fine as long as it is really gone.
            if error and record_id not in self.api.ids(kind, org):
                error = None
            if error:
                failures.append(error)
            else:
                self.deleted.append(f"{kind} {record_id}")
        for kind, org in {(k, o) for k, o, _ in self._watched}:
            leftover = {str(r["id"]) for r in self.api.listing(kind, org)["data"]} - self._before(kind, org)
            if leftover:
                failures.append(f"{kind} still listed after cleanup: {sorted(leftover)}")
        for kind, org in {(k, o) for k, _, o in self._tracked}:
            still = {i for k, i, o in self._tracked if (k, o) == (kind, org)} & self.api.ids(kind, org)
            if still:
                failures.append(f"{kind} still listed after cleanup: {sorted(still)}")
        assert not failures, "Test data was NOT cleaned up from dev:\n  " + "\n  ".join(failures)

    def _before(self, kind, org):
        merged = set()
        for k, o, ids in self._watched:
            if (k, o) == (kind, org):
                merged |= ids
        return merged
