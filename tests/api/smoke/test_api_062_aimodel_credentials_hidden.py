# tests/api/smoke/test_api_062_aimodel_credentials_hidden.py
#
# DataSpaceBackend#314 (DataSpace#358): an AI model provider's saved
# credentials (apiKey, hfAuthToken, apiHeaders) come back only to people who
# can edit the model. Everyone else still reads the published model, with those
# fields null / {}.
#
# Uses a model this test creates, with a dummy key. Not `readonly`: it writes,
# and it runs only where the fix is deployed.

import os
import uuid

import pytest

from tests.api.publications import gql
from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#314")]

OWNER, OUTSIDER = 4, 3  # account 3 is in none of account 4's orgs (see test_api_056)
DUMMY = {"apiKey": "qa-dummy-key-not-a-secret", "hfAuthToken": "hf_qadummynotasecret", "apiHeaders": {"X-Qa": "dummy"}}
READ = "query($id: Int!){ getAiModel(modelId:$id){ id versions { providers { apiKey hfAuthToken apiHeaders } } } }"


def _account(n):
    email, password = os.getenv(f"TEST_EMAIL_{n}"), os.getenv(f"TEST_PASSWORD_{n}")
    if not (email and password):
        pytest.skip(f"TEST_EMAIL_{n}/TEST_PASSWORD_{n} not set")
    return ProviderAPI(email, password)


def _ok(body, name):
    assert "errors" not in body, body["errors"]
    payload = body["data"][name]
    assert payload["success"], payload
    return payload["data"]


@pytest.fixture(scope="module")
def published_model():
    owner = _account(OWNER)
    model = _ok(owner.gql("mutation($i: CreateAIModelInput!){ createAiModel(input:$i){ success errors { nonFieldErrors } data { id } } }",
                          {"i": {"modelType": "TEXT_GENERATION", "provider": "CUSTOM", "name": f"qa-cred-{uuid.uuid4().hex[:10]}",
                                 "displayName": "[qa] credentials visibility", "isPublic": True}}), "createAiModel")
    model_id = int(model["id"])
    try:
        version = _ok(owner.gql("mutation($i: CreateAIModelVersionInput!){ createAiModelVersion(input:$i){ success data { id } } }",
                                {"i": {"modelId": model_id, "version": "1.0"}}), "createAiModelVersion")
        _ok(owner.gql("mutation($i: CreateVersionProviderInput!){ createVersionProvider(input:$i){ success data { id } } }",
                      {"i": {"versionId": int(version["id"]), "provider": "CUSTOM",
                             "apiEndpointUrl": "https://api.example.com/v1/predict", **DUMMY}}), "createVersionProvider")
        _ok(owner.gql("mutation($i: UpdateAIModelInput!){ updateAiModel(input:$i){ success data { id } } }",
                      {"i": {"id": model_id, "status": "ACTIVE"}}), "updateAiModel")
        yield owner, model_id
    finally:
        owner.gql("mutation($id: Int!){ deleteAiModel(modelId:$id){ success } }", {"id": model_id})


def _providers(body):
    assert "errors" not in body, body["errors"]
    model = body["data"]["getAiModel"]
    assert model, "the published model is not readable"
    return [p for v in model["versions"] for p in v["providers"]]


def test_owner_reads_the_saved_credentials(published_model):
    owner, model_id = published_model
    providers = _providers(owner.gql(READ, {"id": model_id}))
    assert providers and all(p["apiKey"] == DUMMY["apiKey"] for p in providers), "the owner lost their saved key"


@pytest.mark.parametrize("caller", ["anonymous", "outsider"])
def test_others_get_no_credentials(published_model, anon_graphql_client, caller):
    _, model_id = published_model
    body = gql(anon_graphql_client, READ, {"id": model_id}) if caller == "anonymous" else _account(OUTSIDER).gql(READ, {"id": model_id})
    leaked = [field for p in _providers(body) for field in DUMMY if p[field] not in (None, {})]
    assert not leaked, f"{caller} can read {sorted(set(leaked))} of a model they cannot edit"
