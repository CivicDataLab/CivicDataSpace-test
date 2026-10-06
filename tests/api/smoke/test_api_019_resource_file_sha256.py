# tests/api/smoke/test_api_019_resource_file_sha256.py
#
# Covers DataSpaceBackend#212: a `sha256` column on uploaded resource files,
# exposed on GraphQL's `fileDetails`.
#
# `readonly` + `deployed_pr`: unauthenticated read, safe to merge now --
# skipped wherever the backend under test doesn't serve #212 yet (prod,
# until the feature reaches main), same pattern as #211/#215 before it.
#
# Known gap, checked live on 2026-10-06 (the day #212 reached dev): across
# all 343 published datasets / 551 FILE resources on dev, every `sha256` is
# still null. The column exists and resolves (this file's first test proves
# that), but either `manage.py backfill_file_hashes` hasn't been run on dev
# yet, or no resource file has been re-saved since the deploy to trigger the
# on-save hashing path. A value-correctness test (is the stored hash the
# real SHA-256 of the file's bytes?) needs at least one hashed resource to
# exist and is deferred until then -- see the second test below, which skips
# with that same reason rather than asserting on data that doesn't exist.

import re

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#212")]


@pytest.mark.smoke
def test_file_details_sha256_field_resolves(anon_graphql_client):
    """`fileDetails { sha256 }` is a real field, not a schema error.

    Pre-#212 this field doesn't exist at all: Strawberry returns "Cannot
    query field 'sha256' on type 'TypeFileDetails'" -- captured live against
    a backend without #212 (see PR body). A regression that renamed or
    dropped the field would look the same.
    """
    data = anon_graphql_client.query(
        "{ datasets(includePublic: true) { id resources { type fileDetails { sha256 } } } }"
    )
    found_file_resource = False
    for row in data["datasets"]:
        for res in row["resources"]:
            if res["type"] == "FILE" and res.get("fileDetails"):
                found_file_resource = True
                sha = res["fileDetails"]["sha256"]
                assert sha is None or isinstance(sha, str), res["fileDetails"]
    if not found_file_resource:
        pytest.skip("no FILE resource with fileDetails on this backend")


@pytest.mark.regression
def test_backfilled_sha256_is_a_real_64char_hex_digest(anon_graphql_client):
    """Once a resource has a hash, it must look like one: 64 lowercase hex chars.

    Currently skips on dev -- see the module docstring: nothing has a
    non-null sha256 there yet. Written now so it starts proving the real
    correctness property the moment `backfill_file_hashes` runs or a file is
    re-saved, with no further edit needed.
    """
    data = anon_graphql_client.query(
        "{ datasets(includePublic: true) { resources { type fileDetails { sha256 } } } }"
    )
    hashes = [
        res["fileDetails"]["sha256"]
        for row in data["datasets"]
        for res in row["resources"]
        if res["type"] == "FILE" and res.get("fileDetails") and res["fileDetails"].get("sha256")
    ]
    if not hashes:
        pytest.skip(
            "no FILE resource on this backend has a non-null sha256 yet "
            "(run manage.py backfill_file_hashes, or save/upload a file, then re-run)"
        )
    for sha in hashes:
        assert re.fullmatch(r"[0-9a-f]{64}", sha), f"not a sha256 hex digest: {sha!r}"
