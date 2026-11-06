# tests/provider/functional/conftest.py
#
# Wizard validation tests reuse one draft per module and delete it afterwards
# through the GraphQL API (fixtures re-exported from tests/api/conftest.py).

import re

import pytest

from tests.api.conftest import api_base_url, keycloak_config, auth_token, graphql_client  # noqa: F401
from tests.api.publications import gql

DELETE = {
    "dataset": "mutation($id: UUID!) { deleteDataset(datasetId: $id) }",
    "usecase": "mutation($id: String!) { deleteUseCase(useCaseId: $id) }",
}
ID_IN_URL = {
    "dataset": re.compile(r"/dataset/([0-9a-f-]{36})/"),
    "usecase": re.compile(r"/usecases/edit/(\d+)/"),
}


@pytest.fixture(scope="module")
def qa_drafts(request):
    """{name: edit URL} shared by a module's tests; every draft is deleted at the end."""
    drafts = {}
    yield drafts
    try:
        client = request.getfixturevalue("graphql_client")
    except BaseException:  # no API credentials: leave the drafts for manual cleanup
        print(f"[qa_drafts] could not delete {list(drafts.values())}")
        return
    for url in drafts.values():
        for kind, pattern in ID_IN_URL.items():
            m = pattern.search(url)
            if m:
                body = gql(client, DELETE[kind], {"id": m.group(1)})
                if body.get("errors"):
                    print(f"[qa_drafts] delete {url} failed: {body['errors']}")


DELETE_WIZ = {
    "collaboratives": "mutation($id: String!) { deleteCollaborative(collaborativeId: $id) }",
    "aimodels": "mutation($id: Int!) { deleteAiModel(modelId: $id) { success } }",
}


@pytest.fixture
def delete_draft_after(graphql_client):  # noqa: F811
    """Call with a wizard URL (/<kind>/edit/<id>/...); the draft is deleted at teardown."""
    urls = []
    yield urls.append
    for url in urls:
        m = re.search(r"/(collaboratives|aimodels)/edit/(\d+)", url)
        if m:
            kind, pk = m.groups()
            graphql_client.query(DELETE_WIZ[kind], {"id": pk if kind == "collaboratives" else int(pk)})
