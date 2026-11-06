# tests/api/functional/test_api_func_005_aimodel_matrix.py
#
# Field-combination and edge-case coverage for AI model, version and provider
# mutations: every model type / provider / domain / lifecycle stage / auth type /
# HTTP method round-trips (pairwise where two enums combine), the one-primary
# and one-latest invariants, uniqueness, and the unchecked bounds and URLs.
# No real credentials: provider keys are a fixed dummy string.

import itertools
import uuid

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

MODEL_TYPES = ["TRANSLATION", "TEXT_GENERATION", "SUMMARIZATION", "QUESTION_ANSWERING", "SENTIMENT_ANALYSIS",
               "TEXT_CLASSIFICATION", "NAMED_ENTITY_RECOGNITION", "TEXT_TO_SPEECH", "SPEECH_TO_TEXT", "OTHER"]
PROVIDERS = ["OPENAI", "LLAMA_OLLAMA", "LLAMA_TOGETHER", "LLAMA_REPLICATE", "LLAMA_CUSTOM", "CUSTOM", "HUGGINGFACE"]
DOMAINS = ["HEALTHCARE", "EDUCATION", "LEGAL", "FINANCE", "AGRICULTURE", "ENVIRONMENT", "GOVERNMENT", "TECHNOLOGY",
           "SCIENCE", "SOCIAL_SERVICES", "TRANSPORTATION", "ENERGY", "GENERAL", "OTHER"]
LIFECYCLE = ["DEVELOPMENT", "TESTING", "BETA", "STAGING", "PRODUCTION", "DEPRECATED", "RETIRED"]
AUTH = ["BEARER", "API_KEY", "BASIC", "OAUTH2", "CUSTOM", "NONE"]
METHODS = ["GET", "POST", "PUT"]
TYPE_PROVIDER = list(zip(MODEL_TYPES, itertools.cycle(PROVIDERS)))
AUTH_METHOD = list(zip(AUTH, itertools.cycle(METHODS)))
DUMMY_KEY = "qa-matrix-dummy-not-a-secret"

RESULT = "success errors { fieldErrors { field messages } nonFieldErrors }"
MODEL = "id name modelType provider domain maxTokens status isPublic"


def _payload(body, name):
    assert "errors" not in body, body["errors"]
    return body["data"][name]


def _failed(payload):
    return not payload["success"]


def _create_model(client, **fields):
    fields = {"modelType": "TEXT_GENERATION", "provider": "CUSTOM",
              "name": f"qa-matrix-{uuid.uuid4().hex[:10]}", "displayName": "[qa-matrix] model", **fields}
    return _payload(gql(client, "mutation($i: CreateAIModelInput!){ createAiModel(input:$i){ %s data { %s } } }" % (RESULT, MODEL),
                        {"i": fields}), "createAiModel")


def _update_model(client, model_id, **fields):
    return _payload(gql(client, "mutation($i: UpdateAIModelInput!){ updateAiModel(input:$i){ %s data { %s } } }" % (RESULT, MODEL),
                        {"i": {"id": model_id, **fields}}), "updateAiModel")


def _read_model(client, model_id):
    body = gql(client, "query($id: Int!){ getAiModel(modelId:$id){ %s versions { id version lifecycleStage isLatest "
                       "providers { id provider isPrimary apiAuthType apiHttpMethod apiTimeoutSeconds apiEndpointUrl } } } }" % MODEL,
               {"id": int(model_id)})
    assert "errors" not in body, body["errors"]
    return body["data"]["getAiModel"]


def _create_version(client, model_id, version, **fields):
    return _payload(gql(client, "mutation($i: CreateAIModelVersionInput!){ createAiModelVersion(input:$i){ %s data { id version isLatest lifecycleStage } } }" % RESULT,
                        {"i": {"modelId": int(model_id), "version": version, **fields}}), "createAiModelVersion")


def _create_provider(client, version_id, **fields):
    fields = {"provider": "CUSTOM", "apiEndpointUrl": "https://api.example.com/v1/predict", "apiKey": DUMMY_KEY, **fields}
    return _payload(gql(client, "mutation($i: CreateVersionProviderInput!){ createVersionProvider(input:$i){ %s data { id isPrimary } } }" % RESULT,
                        {"i": {"versionId": int(version_id), **fields}}), "createVersionProvider")


def _update_provider(client, provider_id, **fields):
    return _payload(gql(client, "mutation($i: UpdateVersionProviderInput!){ updateVersionProvider(input:$i){ %s data { id } } }" % RESULT,
                        {"i": {"id": int(provider_id), **fields}}), "updateVersionProvider")


def _provider(model, provider_id):
    return next(p for v in model["versions"] for p in v["providers"] if str(p["id"]) == str(provider_id))


@pytest.fixture(scope="module")
def model(graphql_client):
    created = _create_model(graphql_client)
    assert created["success"], created["errors"]
    model_id = created["data"]["id"]
    yield model_id
    gql(graphql_client, "mutation($id: Int!){ deleteAiModel(modelId:$id){ success } }", {"id": int(model_id)})


@pytest.fixture(scope="module")
def version(graphql_client, model):
    created = _create_version(graphql_client, model, "1.0")
    assert created["success"], created["errors"]
    return created["data"]["id"]


@pytest.fixture(scope="module")
def provider(graphql_client, version):
    created = _create_provider(graphql_client, version)
    assert created["success"], created["errors"]
    return created["data"]["id"]


# ─── Model ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("model_type,provider_", TYPE_PROVIDER, ids=[t for t, _ in TYPE_PROVIDER])
def test_model_type_and_provider_round_trip(graphql_client, model, model_type, provider_):
    assert not _failed(_update_model(graphql_client, model, modelType=model_type, provider=provider_))
    got = _read_model(graphql_client, model)
    assert (got["modelType"], got["provider"]) == (model_type, provider_)


@pytest.mark.parametrize("domain", DOMAINS)
def test_domain_round_trips(graphql_client, model, domain):
    assert not _failed(_update_model(graphql_client, model, domain=domain))
    assert _read_model(graphql_client, model)["domain"] == domain


def test_name_over_255_is_refused(graphql_client, model):
    before = _read_model(graphql_client, model)["name"]
    assert _failed(_update_model(graphql_client, model, name="n" * 256))
    assert _read_model(graphql_client, model)["name"] == before


def test_same_name_and_version_twice_is_refused(graphql_client):
    name = f"qa-matrix-dup-{uuid.uuid4().hex[:8]}"
    first = _create_model(graphql_client, name=name, version="1")
    try:
        assert first["success"], first["errors"]
        assert _failed(_create_model(graphql_client, name=name, version="1"))
    finally:
        gql(graphql_client, "mutation($id: Int!){ deleteAiModel(modelId:$id){ success } }", {"id": int(first["data"]["id"])})


@pytest.mark.xfail(strict=True, reason="maxTokens has no lower bound; 0 and negatives are stored")
@pytest.mark.parametrize("value", [0, -1])
def test_non_positive_max_tokens_is_refused(graphql_client, model, value):
    assert _failed(_update_model(graphql_client, model, maxTokens=value))


def test_max_tokens_above_int32_is_refused(graphql_client, model):
    body = gql(graphql_client, "mutation($i: UpdateAIModelInput!){ updateAiModel(input:$i){ success } }",
               {"i": {"id": model, "maxTokens": 2 ** 31}})
    assert "errors" in body or not body["data"]["updateAiModel"]["success"]


# ─── Versions ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("stage", LIFECYCLE)
def test_lifecycle_stage_round_trips(graphql_client, model, version, stage):
    body = gql(graphql_client, "mutation($i: UpdateAIModelVersionInput!){ updateAiModelVersion(input:$i){ %s } }" % RESULT,
               {"i": {"id": int(version), "lifecycleStage": stage}})
    assert not _failed(_payload(body, "updateAiModelVersion"))
    got = next(v for v in _read_model(graphql_client, model)["versions"] if str(v["id"]) == str(version))
    assert got["lifecycleStage"] == stage


def test_duplicate_version_label_is_refused(graphql_client, model, version):
    assert _failed(_create_version(graphql_client, model, "1.0"))


def test_only_one_version_is_latest(graphql_client, model, version):
    created = _create_version(graphql_client, model, f"2.{uuid.uuid4().hex[:3]}")
    assert created["success"], created["errors"]
    latest = [v for v in _read_model(graphql_client, model)["versions"] if v["isLatest"]]
    assert [str(v["id"]) for v in latest] == [str(created["data"]["id"])]


def test_version_label_over_50_is_refused(graphql_client, model):
    assert _failed(_create_version(graphql_client, model, "v" * 51))


# ─── Providers ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("auth,method", AUTH_METHOD, ids=[a for a, _ in AUTH_METHOD])
def test_auth_type_and_method_round_trip(graphql_client, model, provider, auth, method):
    assert not _failed(_update_provider(graphql_client, provider, apiAuthType=auth, apiHttpMethod=method))
    got = _provider(_read_model(graphql_client, model), provider)
    assert (got["apiAuthType"], got["apiHttpMethod"]) == (auth, method)


def test_only_one_provider_is_primary(graphql_client, model, version, provider):
    second = _create_provider(graphql_client, version, provider="OPENAI", isPrimary=True)
    assert second["success"], second["errors"]
    primaries = [p for v in _read_model(graphql_client, model)["versions"] if str(v["id"]) == str(version)
                 for p in v["providers"] if p["isPrimary"]]
    assert [str(p["id"]) for p in primaries] == [str(second["data"]["id"])]


@pytest.mark.xfail(strict=True, reason="apiEndpointUrl is never validated; any string is stored")
@pytest.mark.parametrize("url", ["not a url", "javascript:alert(1)"])
def test_invalid_endpoint_url_is_refused(graphql_client, provider, url):
    assert _failed(_update_provider(graphql_client, provider, apiEndpointUrl=url))


@pytest.mark.xfail(strict=True, reason="apiTimeoutSeconds has no lower bound; 0 and negatives are stored")
@pytest.mark.parametrize("value", [0, -5])
def test_non_positive_timeout_is_refused(graphql_client, provider, value):
    assert _failed(_update_provider(graphql_client, provider, apiTimeoutSeconds=value))


def test_endpoint_url_over_500_is_refused(graphql_client, provider):
    assert _failed(_update_provider(graphql_client, provider, apiEndpointUrl="https://example.com/" + "p" * 500))
