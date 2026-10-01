# tests/api/smoke/test_api_014_publication_blocks_schema.py
#
# Covers DataSpaceBackend#214 ("Enhance publication management with title
# and description fields for blocks") via GraphQL introspection.
#
# All of this PR's actual behaviour changes are write-side and
# auth-gated: creating a draft publication with optional fields, adding a
# YouTube/file block with a title/description, and the new
# updatePublicationBlock mutation all require a logged-in org member. This
# is a cloud run with no test credentials, so none of that can be executed
# here — see the PR body for what a human needs to run to confirm it.
#
# What CAN be proven without auth: the public GraphQL schema itself changed
# to support it. Introspection is unauthenticated and reflects the live
# schema, so these checks are a genuine (if partial) red/green proof — not
# a placeholder.

import pytest

pytestmark = [pytest.mark.api]


def _type_fields(anon_graphql_client, type_name):
    data = anon_graphql_client.query(
        '{ __type(name: "%s") { name kind fields { name } inputFields { name } } }' % type_name
    )
    return data["__type"]


@pytest.mark.smoke
def test_publication_block_type_has_title_description_created(anon_graphql_client):
    """TypePublicationBlock now exposes title, description and created
    (DataSpaceBackend#214's migration 0048 + type_publication.py change)."""
    type_info = _type_fields(anon_graphql_client, "TypePublicationBlock")
    assert type_info, "TypePublicationBlock is missing from the schema"
    field_names = {f["name"] for f in type_info["fields"]}
    for expected in ("title", "description", "created"):
        assert expected in field_names, (
            f"TypePublicationBlock.{expected} missing — got fields: {sorted(field_names)}"
        )


@pytest.mark.functional
def test_update_publication_block_mutation_exists(anon_graphql_client):
    """The new `updatePublicationBlock` mutation is registered on the schema."""
    data = anon_graphql_client.query("{ __type(name: \"Mutation\") { fields { name } } }")
    mutation_names = {f["name"] for f in data["__type"]["fields"]}
    for expected in ("updatePublicationBlock", "addPublicationFileBlock", "addPublicationYoutubeBlock"):
        assert expected in mutation_names, (
            f"Mutation.{expected} missing — got: {sorted(mutation_names)}"
        )


@pytest.mark.regression
def test_create_publication_input_fields_are_all_optional(anon_graphql_client):
    """Every CreatePublicationInput field is nullable (DataSpaceBackend#214
    made drafts creatable with partial or no metadata; `publishPublication`,
    not `createPublication`, now enforces the required fields).

    Before #214, `title`/`description`/`authors`/`publicationDate`/`license`/
    `resourceTypeId` were NON_NULL (required) on this input. A regression
    that reintroduces a required field here would break a client that
    creates a bare/empty draft, which #214's own tests
    (test_empty_input_creates_a_draft) rely on.
    """
    type_info = _type_fields(anon_graphql_client, "CreatePublicationInput")
    assert type_info, "CreatePublicationInput is missing from the schema"
    required_now = [
        f["name"] for f in type_info["inputFields"]
        if f["name"] in {
            "title", "description", "authors", "publicationDate",
            "license", "resourceTypeId",
        }
    ]
    # (introspection only reports NON_NULL via `type.kind`, fetched separately
    # to keep this query — and the failure message — readable)
    kinds = anon_graphql_client.query(
        """
        { __type(name: "CreatePublicationInput") {
            inputFields { name type { kind } }
          } }
        """
    )["__type"]["inputFields"]
    non_null = {f["name"] for f in kinds if f["type"]["kind"] == "NON_NULL"}
    still_required = non_null & {
        "title", "description", "authors", "publicationDate",
        "license", "resourceTypeId",
    }
    assert not still_required, (
        f"CreatePublicationInput has fields that should be optional but are "
        f"still NON_NULL: {sorted(still_required)}"
    )
    assert required_now  # sanity: the fields we're checking actually exist
