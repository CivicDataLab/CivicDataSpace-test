# tests/provider/functional/conftest.py
#
# Wizard validation tests reuse one draft per module and delete it afterwards
# through the GraphQL API (fixtures re-exported from tests/api/conftest.py).

import re

import pytest


DELETE = {
    "dataset": "mutation($id: UUID!) { deleteDataset(datasetId: $id) }",
    "usecase": "mutation($id: String!) { deleteUseCase(useCaseId: $id) }",
}
ID_IN_URL = {
    "dataset": re.compile(r"/dataset/([0-9a-f-]{36})/"),
    "usecase": re.compile(r"/usecases/edit/(\d+)/"),
}


CREATE = {
    "data": ("mutation{ addDataset(createInput: {datasetType: DATA}){ success data { id } } }", "addDataset", "dataset/{id}/edit/metadata"),
    "prompt": ("mutation{ addDataset(createInput: {datasetType: PROMPT}){ success data { id } } }", "addDataset", "dataset/{id}/edit/metadata"),
    "uc": ("mutation{ addUseCase { ... on TypeUseCase { id } } }", "addUseCase", "usecases/edit/{id}/details"),
}
DASHBOARD_BASE = re.compile(r"(https?://[^/]+(?:/[a-z]{2})?/dashboard/[^/]+/[^/]+)")


class Drafts(dict):
    """{name: edit URL}. `create` makes a draft through the API (the same mutation the
    UI button sends) and returns its edit URL, or None when there are no API credentials."""

    client = None

    def create(self, kind, driver):
        if self.client is None:
            return None
        query, field, path = CREATE[kind]
        body = self.client.gql(query)
        created = (body.get("data") or {}).get(field) or {}
        draft_id = (created.get("data") or created).get("id")
        assert draft_id, f"API could not create a {kind} draft: {body}"
        base = DASHBOARD_BASE.search(driver.current_url).group(1)
        return f"{base}/{path.format(id=draft_id)}"


@pytest.fixture(scope="module")
def qa_drafts(request):
    """{name: edit URL} shared by a module's tests; every draft is deleted at the end."""
    drafts = Drafts()
    try:
        drafts.client = request.getfixturevalue("provider_api")
    except BaseException:  # no API credentials: fall back to creating drafts in the UI
        pass
    yield drafts
    try:
        client = request.getfixturevalue("provider_api")
    except BaseException:  # no API credentials: leave the drafts for manual cleanup
        print(f"[qa_drafts] could not delete {list(drafts.values())}")
        return
    for url in drafts.values():
        for kind, pattern in ID_IN_URL.items():
            m = pattern.search(url)
            if m:
                body = client.gql(DELETE[kind], {"id": m.group(1)})
                if body.get("errors"):
                    print(f"[qa_drafts] delete {url} failed: {body['errors']}")


DELETE_WIZ = {
    "collaboratives": "mutation($id: String!) { deleteCollaborative(collaborativeId: $id) }",
    "aimodels": "mutation($id: Int!) { deleteAiModel(modelId: $id) { success } }",
}


@pytest.fixture
def delete_draft_after(provider_api):
    """Call with a wizard URL (/<kind>/edit/<id>/...); the draft is deleted at teardown."""
    urls = []
    yield urls.append
    for url in urls:
        m = re.search(r"/(collaboratives|aimodels)/edit/(\d+)", url)
        if m:
            kind, pk = m.groups()
            provider_api.gql(DELETE_WIZ[kind], {"id": pk if kind == "collaboratives" else int(pk)})
