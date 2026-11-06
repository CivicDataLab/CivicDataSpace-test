# tests/api/functional/test_api_func_007_prompt_dataset_matrix.py
#
# Prompt-dataset metadata combinations: every task type paired with a purpose,
# languages / model types / domain round-trips, and the prompt-resource details
# (format, counts) including the values the API accepts without checking.

import itertools
import json

import pytest
import requests

from tests.api.client import _request_with_retries
from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

TASKS = ["TEXT_GENERATION", "TEXT_CLASSIFICATION", "QUESTION_ANSWERING", "SUMMARIZATION", "TRANSLATION",
         "SENTIMENT_ANALYSIS", "NAMED_ENTITY_RECOGNITION", "CODE_GENERATION", "CONVERSATION",
         "INSTRUCTION_FOLLOWING", "REASONING", "CREATIVE_WRITING", "DATA_EXTRACTION", "OTHER"]
PURPOSES = ["RESEARCH", "EDUCATION", "EVALUATION", "OTHER"]
FORMATS = ["INSTRUCTION", "CHAT", "COMPLETION", "FEW_SHOT", "CHAIN_OF_THOUGHT", "ZERO_SHOT", "OTHER"]
TASK_PURPOSE = list(zip(TASKS, itertools.cycle(PURPOSES)))

META = "mutation($i: UpdatePromptMetadataInput!){ updatePromptMetadata(updateInput:$i){ success } }"
RES = "mutation($i: UpdatePromptResourceInput!){ updatePromptResource(updateInput:$i){ success } }"
READ = "query($id: UUID!){ getDataset(datasetId:$id){ promptMetadata resources { id promptDetails { promptFormat hasSystemPrompt hasExampleResponses avgPromptLength promptCount } } } }"
PROMPT_CSV = b"prompt,response\nWhat is 2+2?,4\nCapital of Assam?,Dispur\n"


def _ok(body, name):
    assert "errors" not in body, body["errors"]
    return body["data"][name]["success"]


def _read(client, dataset_id):
    body = gql(client, READ, {"id": dataset_id})
    assert "errors" not in body, body["errors"]
    return body["data"]["getDataset"]


@pytest.fixture(scope="module")
def prompt_dataset(graphql_client, api_base_url, auth_token):
    body = gql(graphql_client, "mutation{ addDataset(createInput:{datasetType: PROMPT}){ data { id } } }")
    dataset_id = body["data"]["addDataset"]["data"]["id"]
    operations = {"query": "mutation($i: CreateFileResourceInput!){ createFileResources(fileResourceInput:$i){ id } }",
                  "variables": {"i": {"dataset": dataset_id, "files": [None]}}}
    resp = _request_with_retries(
        requests.post, f"{api_base_url.rstrip('/')}/api/graphql", headers={"Authorization": f"Bearer {auth_token}"},
        data={"operations": json.dumps(operations), "map": json.dumps({"0": ["variables.i.files.0"]})},
        files={"0": ("prompts.csv", PROMPT_CSV)},
    )
    resource_id = resp.json()["data"]["createFileResources"][0]["id"]
    yield dataset_id, resource_id
    gql(graphql_client, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": dataset_id})


@pytest.mark.parametrize("task,purpose", TASK_PURPOSE, ids=[t for t, _ in TASK_PURPOSE])
def test_task_type_and_purpose_round_trip(graphql_client, prompt_dataset, task, purpose):
    dataset_id, _ = prompt_dataset
    assert _ok(gql(graphql_client, META, {"i": {"dataset": dataset_id, "taskType": task, "purpose": purpose}}), "updatePromptMetadata")
    meta = _read(graphql_client, dataset_id)["promptMetadata"]
    assert meta["task_type"] == task, meta


@pytest.mark.xfail(strict=True, reason="purpose is saved by updatePromptMetadata but promptMetadata never returns it")
def test_purpose_is_readable(graphql_client, prompt_dataset):
    dataset_id, _ = prompt_dataset
    gql(graphql_client, META, {"i": {"dataset": dataset_id, "purpose": "EVALUATION"}})
    assert _read(graphql_client, dataset_id)["promptMetadata"].get("purpose") == "EVALUATION"


def test_languages_model_types_and_domain_round_trip(graphql_client, prompt_dataset):
    dataset_id, _ = prompt_dataset
    fields = {"targetLanguages": ["ENGLISH", "HINDI", "ASSAMESE"], "targetModelTypes": ["GPT", "INDIC_LLM"],
              "domain": "HEALTHCARE", "evaluationCriteria": {"accuracy": 0.9, "notes": "qa-matrix"}}
    assert _ok(gql(graphql_client, META, {"i": {"dataset": dataset_id, **fields}}), "updatePromptMetadata")
    meta = _read(graphql_client, dataset_id)["promptMetadata"]
    assert meta["target_languages"] == fields["targetLanguages"]
    assert meta["target_model_types"] == fields["targetModelTypes"]
    assert meta["domain"] == "HEALTHCARE"


@pytest.mark.xfail(strict=True, reason="domain is a free String; values outside PromptDomain are stored")
def test_unknown_domain_is_refused(graphql_client, prompt_dataset):
    dataset_id, _ = prompt_dataset
    assert not _ok(gql(graphql_client, META, {"i": {"dataset": dataset_id, "domain": "NOT_A_DOMAIN"}}), "updatePromptMetadata")


@pytest.mark.parametrize("fmt", FORMATS)
def test_prompt_format_round_trips(graphql_client, prompt_dataset, fmt):
    dataset_id, resource_id = prompt_dataset
    assert _ok(gql(graphql_client, RES, {"i": {"resource": resource_id, "promptFormat": fmt,
                                              "hasSystemPrompt": True, "hasExampleResponses": False,
                                              "avgPromptLength": 42, "promptCount": 2}}), "updatePromptResource")
    details = _read(graphql_client, dataset_id)["resources"][0]["promptDetails"]
    assert details == {"promptFormat": fmt, "hasSystemPrompt": True, "hasExampleResponses": False,
                       "avgPromptLength": 42, "promptCount": 2}


@pytest.mark.xfail(strict=True, reason="promptFormat is a free String; values outside PromptFormat are stored")
def test_unknown_prompt_format_is_refused(graphql_client, prompt_dataset):
    _, resource_id = prompt_dataset
    assert not _ok(gql(graphql_client, RES, {"i": {"resource": resource_id, "promptFormat": "NOT_A_FORMAT"}}), "updatePromptResource")


@pytest.mark.xfail(strict=True, reason="promptCount / avgPromptLength accept negative numbers")
def test_negative_counts_are_refused(graphql_client, prompt_dataset):
    _, resource_id = prompt_dataset
    assert not _ok(gql(graphql_client, RES, {"i": {"resource": resource_id, "promptCount": -1, "avgPromptLength": -5}}), "updatePromptResource")
