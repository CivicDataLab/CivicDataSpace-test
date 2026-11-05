# tests/api/publications.py
#
# Helpers for the publication API tests (DataSpace#243). Publication mutations
# always return HTTP 200 and report failure in `success` / `errors`, so the
# helpers return the mutation payload and leave the asserting to the tests.

import json
import uuid

import pytest

RESULT = "success errors { fieldErrors { field messages } nonFieldErrors }"
PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
)


def gql(client, query, variables=None, org=None):
    """POST a query and return the whole body, top-level `errors` included.

    `org` sends the `organization` header for this request only, so the shared
    session client is left untouched.
    """
    headers = {"organization": org} if org else {}
    resp = client.session.post(
        client.endpoint, json={"query": query, "variables": variables or {}}, headers=headers, timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def mutate(client, name, query, variables=None, org=None):
    """Run a publication mutation and return its payload ({success, errors, data})."""
    body = gql(client, query, variables, org)
    assert "errors" not in body, f"{name}: GraphQL errors {body['errors']}"
    return body["data"][name]


def unique_title(prefix="api test"):
    return f"{prefix} {uuid.uuid4().hex[:8]}"


def create(client, org=None, **fields):
    """Create a draft and return its data. List fields default to empty."""
    fields = {"authors": [], "sectorIds": [], "geographyIds": [], **fields}
    payload = mutate(
        client, "createPublication",
        "mutation($i: CreatePublicationInput!){ createPublication(input:$i){ %s "
        "data { id title slug status license authors description isIndividualPublication "
        "organization { name } } } }" % RESULT,
        {"i": fields}, org,
    )
    assert payload["success"], f"createPublication failed: {payload['errors']}"
    return payload["data"]


def update(client, publication_id, org=None, **fields):
    return mutate(
        client, "updatePublication",
        "mutation($i: UpdatePublicationInput!){ updatePublication(input:$i){ %s "
        "data { id title description authors } } }" % RESULT,
        {"i": {"id": publication_id, **fields}}, org,
    )


def delete(client, publication_id, org=None):
    return mutate(
        client, "deletePublication",
        "mutation($id: UUID!){ deletePublication(publicationId:$id){ %s } }" % RESULT,
        {"id": publication_id}, org,
    )


def publish(client, publication_id, org=None):
    return mutate(
        client, "publishPublication",
        "mutation($id: UUID!){ publishPublication(publicationId:$id){ %s data { id status } } }" % RESULT,
        {"id": publication_id}, org,
    )


def get(client, publication_id):
    """Return the whole getPublication body (data may be null with an error)."""
    return gql(
        client,
        "query($id: UUID!){ getPublication(publicationId:$id){ id title description authors status "
        "blocks { id position blockType title description fileName youtubeVideoId } } }",
        {"id": publication_id},
    )


def blocks(client, publication_id):
    return get(client, publication_id)["data"]["getPublication"]["blocks"]


def add_youtube(client, publication_id, url, title=None, description=None):
    return mutate(
        client, "addPublicationYoutubeBlock",
        "mutation($id: UUID!, $u: String!, $t: String, $d: String){ addPublicationYoutubeBlock("
        "publicationId:$id, youtubeUrl:$u, title:$t, description:$d){ %s "
        "data { id position youtubeVideoId title description } } }" % RESULT,
        {"id": publication_id, "u": url, "t": title, "d": description},
    )


def upload(client, mutation, field_args, file_name, content):
    """Multipart GraphQL upload (graphql-multipart-request-spec), one file as `$file`."""
    operations = {"query": mutation, "variables": {**field_args, "file": None}}
    resp = client.session.post(
        client.endpoint,
        data={"operations": json.dumps(operations), "map": json.dumps({"0": ["variables.file"]})},
        files={"0": (file_name, content)},
        # The session defaults to application/json; requests must set the multipart boundary.
        headers={"Content-Type": None},
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    assert "errors" not in body, f"upload: GraphQL errors {body['errors']}"
    return next(iter(body["data"].values()))


def add_file(client, publication_id, file_name, content):
    return upload(
        client,
        "mutation($id: UUID!, $file: Upload!){ addPublicationFileBlock(publicationId:$id, file:$file){ %s "
        "data { id position fileName title blockType } } }" % RESULT,
        {"id": publication_id}, file_name, content,
    )


def errors_of(payload):
    """Flatten a payload's errors to {field or None: [messages]}."""
    errors = payload.get("errors") or {}
    out = {}
    for item in errors.get("fieldErrors") or []:
        out[item["field"]] = item["messages"]
    if errors.get("nonFieldErrors"):
        out[None] = errors["nonFieldErrors"]
    return out


def org_slug(client, name):
    orgs = gql(client, "{ organizations { name slug } }")["data"]["organizations"]
    slug = next((o["slug"] for o in orgs if o["name"] == name), None)
    assert slug, f"organization {name!r} not found"
    return slug


def unpublish(client, publication_id, org=None):
    return mutate(
        client, "unpublishPublication",
        "mutation($id: UUID!){ unpublishPublication(publicationId:$id){ %s data { id status } } }" % RESULT,
        {"id": publication_id}, org,
    )


def complete_fields(client):
    """Every field publishing needs, with live resource type / sector / geography ids."""
    lookups = gql(client, "{ resourceTypes { id } activeSectors(pagination: {limit: 1}) { id } geographies { id } }")["data"]
    if not lookups["resourceTypes"]:
        pytest.skip("no active resource types on this backend, so nothing can be published (DataSpaceBackend#217)")
    return {
        "title": unique_title("publish test"),
        "description": "Publication API test",
        "authors": ["A. Author"],
        "publicationDate": "2024-01-01",
        "resourceTypeId": lookups["resourceTypes"][0]["id"],
        "sectorIds": [lookups["activeSectors"][0]["id"]],
        "geographyIds": [int(lookups["geographies"][0]["id"])],
    }
