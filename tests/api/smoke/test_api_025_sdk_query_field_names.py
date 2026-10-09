# tests/api/smoke/test_api_025_sdk_query_field_names.py
#
# Pending: covers open CivicDataLab/DataSpaceBackend#52 (head `97260a8`,
# "Dataspace sdk" — "Corrected the get ai model graphql query in sdk"),
# open since 2025-12-16, base `dev`. Skipped in CI until it merges. Safe to
# merge before it.
#
# `dataspace_sdk/resources/aimodels.py` and `datasets.py` (a Python client
# SDK that lives inside the DataSpaceBackend repo) hardcode GraphQL query
# strings. Before #52 they queried the schema's `aiModel`/`dataset`
# top-level fields with `createdAt`/`title`-on-resources-style sub-fields —
# field names that do not exist on the live schema. Confirmed live on dev
# right now, independent of this PR merging:
#
#   query GetAIModel($id: UUID!) { aiModel(id: $id) { id name } }
#   -> "Cannot query field 'aiModel' on type 'Query'. Did you mean
#      'aiModels' or 'getAiModel'?"
#
#   query GetDataset($id: UUID!) { dataset(id: $id) { id title createdAt } }
#   -> "Cannot query field 'dataset' on type 'Query'. Did you mean
#      'datasets' or 'getDataset'?"
#
# #52's fix switches to the schema's real `getAiModel(modelId: Int!)` /
# `getDataset(datasetId: UUID!)` fields with their real sub-field shapes
# (`created`/`modified` instead of `createdAt`/`updatedAt`, `resources.name`
# instead of `resources.title`, `fileDetails`/`schema` as objects, …).
#
# Nothing is deployed anywhere when a client SDK PR merges — the backend
# already has these fields today, unrelated to #52 merging. So there is no
# server-side "before/after" to gate on. What this covers instead: whether
# the SDK's *query text* is schema-valid, using the PR's exact new query
# strings (copied from the diff, not paraphrased). Gated with `pending_pr`
# because that query text only exists in the DataSpaceBackend repo once #52
# merges — not because the schema check itself depends on the merge.
#
# A nonexistent id is used deliberately in both: this checks field *names*
# on the schema, not any specific record, so it can't be broken by data
# changing out from under it.
#
# Never `readonly` — this is the pending_pr gate (skips until #52 merges to
# `dev`), not the readonly prod-safety gate from the merged-PR flow.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.pending_pr("DataSpaceBackend#52")]

# Copied verbatim from dataspace_sdk/resources/aimodels.py at PR#52 head (97260a8).
AIMODEL_QUERY = """
query GetAIModel($id: Int!) {
    getAiModel(modelId: $id) {
        id
        name
        displayName
        description
        modelType
        provider
        version
        providerModelId
        hfUsePipeline
        hfAuthToken
        hfModelClass
        hfAttnImplementation
        framework
        supportsStreaming
        maxTokens
        supportedLanguages
        inputSchema
        outputSchema
        status
        isPublic
        createdAt
        updatedAt
        organization {
            id
            name
        }
        tags {
            id
            value
        }
        sectors {
            id
            name
        }
        geographies {
            id
            name
        }
        endpoints {
            id
            url
            httpMethod
            authType
            isActive
        }
    }
}
"""

# Copied verbatim from dataspace_sdk/resources/datasets.py at PR#52 head (97260a8).
DATASET_QUERY = """
query GetDataset($id: UUID!) {
    getDataset(datasetId: $id) {
        id
        title
        description
        status
        accessType
        license
        created
        modified
        organization {
            id
            name
            description
        }
        tags {
            id
            value
        }
        sectors {
            id
            name
        }
        geographies {
            id
            name
        }
        resources {
            id
            name
            description
            fileDetails {
              format
            }
            schema {
              fieldName
            }
            created
            modified
        }
    }
}
"""


def _schema_errors(errors):
    """GraphQL errors that mean a field/type does not exist on the schema,
    as opposed to an app-level permission/not-found error (which is a
    legitimate outcome for a nonexistent id and not what this test is
    about)."""
    return [e for e in errors if "Cannot query field" in e.get("message", "")]


def test_sdk_aimodel_query_matches_live_schema(anon_api_client):
    """PR#52's new AI-model query (getAiModel(modelId: Int!) with its full
    sub-field shape) must be schema-valid against the live GraphQL endpoint."""
    resp = anon_api_client.post(
        "/api/graphql",
        json={"query": AIMODEL_QUERY, "variables": {"id": 999999999}},
    )
    assert resp.status_code == 200, f"GraphQL request failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    schema_errors = _schema_errors(body.get("errors") or [])
    assert not schema_errors, (
        f"dataspace_sdk's getAiModel query (PR#52) is not schema-valid: {schema_errors}"
    )


def test_sdk_dataset_query_matches_live_schema(anon_api_client):
    """PR#52's new dataset query (getDataset(datasetId: UUID!) with its full
    sub-field shape) must be schema-valid against the live GraphQL endpoint."""
    resp = anon_api_client.post(
        "/api/graphql",
        json={
            "query": DATASET_QUERY,
            "variables": {"id": "00000000-0000-0000-0000-000000000000"},
        },
    )
    assert resp.status_code == 200, f"GraphQL request failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    schema_errors = _schema_errors(body.get("errors") or [])
    assert not schema_errors, (
        f"dataspace_sdk's getDataset query (PR#52) is not schema-valid: {schema_errors}"
    )
