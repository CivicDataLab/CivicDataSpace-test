# tests/api/smoke/test_api_053_canonical_url_slug_redirect.py
#
# Covers DataSpaceFrontend#524 ("Refactor AI model and dataset components to
# utilize public URLs Slug", merge e4f3783d9f9ca9236e85986d54a17933bb5f92ff)
# and #525 ("...to utilize separate query files", merge
# 8c4d7c62a7d555870677c9c4e76a638fdc2e7e9e) — both on `provider-flow-update`,
# merged into DataSpaceFrontend `dev` ~80 minutes apart, #525 being a
# same-day refactor of #524's own feature. Treated as one coverage unit: the
# behaviour that survived into the final, deployed state is what's tested.
#
# What changed, from the diff (lib/public-link.ts, app/.../[modelId]/page.tsx,
# app/.../[datasetIdentifier]/page.tsx, app/.../[useCaseSlug]/page.tsx):
# datasets, AI models and use cases are now addressed by a human-readable
# `urlSlug`. Visiting the OLD address (the dataset's raw UUID, or an AI
# model's/use case's raw integer id) 308-redirects to the canonical
# `/<section>/<urlSlug>` address; visiting the urlSlug address directly
# serves the page with no further redirect.
#
# Read-only, anonymous (public detail pages) — no credentials needed.
#
# Gated with `deployed_pr`, not `readonly`. This is a dev-only feature so far:
# `git merge-base --is-ancestor 8c4d7c62a7d555870677c9c4e76a638fdc2e7e9e
# origin/main` on DataSpaceFrontend is false as of this PR, and the prod
# backend's GraphQL schema has no `urlSlug` field at all (confirmed live:
# querying it on https://api.datakeep.civicdays.in returns "Cannot query
# field 'urlSlug' on type 'TypeDataset'"). Putting `readonly` on this file
# would fail every DataSpaceBackend/DataSpaceFrontend `main` deploy's smoke
# gate until the feature ships. Follow-up once it does: add `readonly` here.
#
# Red/green proof (see PR body for the full pasted runs):
#   - GREEN today, on dev (HOME_URL_DEV=https://dev.civicdataspace.in): the
#     legacy-id tests 308-redirect, the canonical-slug tests serve 200.
#   - RED today, on prod (HOME_URL_DEV=https://civicdataspace.in,
#     API_BASE_URL=https://api.datakeep.civicdays.in), which still runs the
#     pre-#524 code: the exact same legacy-id requests return 200 with no
#     redirect at all — prod has not shipped the canonical-slug feature, so
#     there is nothing to redirect to. This is a real "parent commit" red
#     run (prod serves the code before the change), not a flipped assertion.
#     Only the legacy-id tests are safe to run this way: the canonical-slug
#     tests query the backend for `urlSlug`, which prod's schema doesn't have.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke]


# ─── fixtures: pick real published records at runtime ──────────────────────


@pytest.fixture(scope="module")
def published_dataset_id(anon_graphql_client):
    """A published dataset's raw id (UUID) — a field present on every schema
    version, so this fixture (unlike the ones below) is safe to run against
    prod for the red proof."""
    data = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 20}) { id status } }"
    )
    for d in data["datasets"]:
        if d["status"] == "PUBLISHED":
            return d["id"]
    pytest.skip("No published dataset on this environment")


@pytest.fixture(scope="module")
def published_aimodel_id(anon_graphql_client):
    data = anon_graphql_client.query(
        "{ aiModels(filters: {isPublic: true, status: ACTIVE}) { id } }"
    )
    models = data.get("aiModels") or []
    if not models:
        pytest.skip("No published AI model on this environment")
    return models[0]["id"]


@pytest.fixture(scope="module")
def published_usecase_id(anon_graphql_client):
    data = anon_graphql_client.query("{ publishedUseCases { id } }")
    cases = data.get("publishedUseCases") or []
    if not cases:
        pytest.skip("No published use case on this environment")
    return cases[0]["id"]


@pytest.fixture(scope="module")
def dataset_with_distinct_slug(anon_graphql_client):
    """A published dataset whose urlSlug differs from its raw id. dev-only:
    `urlSlug` doesn't exist on prod's schema (see module docstring)."""
    data = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 20}) "
        "{ id urlSlug status } }"
    )
    for d in data["datasets"]:
        if d["status"] == "PUBLISHED" and d.get("urlSlug") and d["urlSlug"] != d["id"]:
            return d
    pytest.skip("No published dataset with a urlSlug distinct from its id")


@pytest.fixture(scope="module")
def aimodel_with_distinct_slug(anon_graphql_client):
    data = anon_graphql_client.query(
        "{ aiModels(filters: {isPublic: true, status: ACTIVE}) { id urlSlug } }"
    )
    for m in data.get("aiModels") or []:
        if m.get("urlSlug") and m["urlSlug"] != str(m["id"]):
            return m
    pytest.skip("No published AI model with a urlSlug distinct from its id")


@pytest.fixture(scope="module")
def usecase_with_distinct_slug(anon_graphql_client):
    data = anon_graphql_client.query("{ publishedUseCases { id urlSlug } }")
    for u in data.get("publishedUseCases") or []:
        if u.get("urlSlug") and u["urlSlug"] != str(u["id"]):
            return u
    pytest.skip("No published use case with a urlSlug distinct from its id")


# ─── legacy raw-id address: must 308 to a different, canonical address ─────


@pytest.mark.deployed_pr("DataSpaceFrontend#525", site="HOME_URL_DEV")
def test_dataset_legacy_id_redirects_to_canonical_slug(
    dev_frontend_client, published_dataset_id
):
    resp = dev_frontend_client.get(
        f"/datasets/{published_dataset_id}", allow_redirects=False
    )
    assert resp.status_code == 308, (
        f"expected a 308 permanent redirect off the raw dataset id "
        f"{published_dataset_id!r}, got {resp.status_code}. The canonical-slug "
        f"redirect (lib/public-link.ts, DataSpaceFrontend#524/#525) may be missing "
        f"or have regressed."
    )
    location = resp.headers.get("Location", "")
    assert location and not location.rstrip("/").endswith(
        f"/datasets/{published_dataset_id}"
    ), (
        f"redirected to {location!r}, which still ends in the raw dataset id — "
        f"not a real canonical-slug redirect"
    )


@pytest.mark.deployed_pr("DataSpaceFrontend#525", site="HOME_URL_DEV")
def test_aimodel_legacy_id_redirects_to_canonical_slug(
    dev_frontend_client, published_aimodel_id
):
    resp = dev_frontend_client.get(
        f"/aimodels/{published_aimodel_id}", allow_redirects=False
    )
    assert resp.status_code == 308, (
        f"expected a 308 permanent redirect off the raw AI model id "
        f"{published_aimodel_id!r}, got {resp.status_code}."
    )
    location = resp.headers.get("Location", "")
    assert location and not location.rstrip("/").endswith(
        f"/aimodels/{published_aimodel_id}"
    ), f"redirected to {location!r}, which still ends in the raw AI model id"


@pytest.mark.deployed_pr("DataSpaceFrontend#525", site="HOME_URL_DEV")
def test_usecase_legacy_id_redirects_to_canonical_slug(
    dev_frontend_client, published_usecase_id
):
    resp = dev_frontend_client.get(
        f"/usecases/{published_usecase_id}", allow_redirects=False
    )
    assert resp.status_code == 308, (
        f"expected a 308 permanent redirect off the raw use case id "
        f"{published_usecase_id!r}, got {resp.status_code}."
    )
    location = resp.headers.get("Location", "")
    assert location and not location.rstrip("/").endswith(
        f"/usecases/{published_usecase_id}"
    ), f"redirected to {location!r}, which still ends in the raw use case id"


# ─── canonical urlSlug address: must serve directly, no further redirect ───


@pytest.mark.deployed_pr("DataSpaceFrontend#525", site="HOME_URL_DEV")
def test_dataset_canonical_slug_serves_without_redirecting(
    dev_frontend_client, dataset_with_distinct_slug
):
    resp = dev_frontend_client.get(
        f"/datasets/{dataset_with_distinct_slug['urlSlug']}", allow_redirects=False
    )
    assert resp.status_code == 200, (
        f"canonical dataset url /datasets/{dataset_with_distinct_slug['urlSlug']} "
        f"did not serve directly, got {resp.status_code} "
        f"(Location: {resp.headers.get('Location')!r})"
    )


@pytest.mark.deployed_pr("DataSpaceFrontend#525", site="HOME_URL_DEV")
def test_aimodel_canonical_slug_serves_without_redirecting(
    dev_frontend_client, aimodel_with_distinct_slug
):
    resp = dev_frontend_client.get(
        f"/aimodels/{aimodel_with_distinct_slug['urlSlug']}", allow_redirects=False
    )
    assert resp.status_code == 200, (
        f"canonical AI model url /aimodels/{aimodel_with_distinct_slug['urlSlug']} "
        f"did not serve directly, got {resp.status_code} "
        f"(Location: {resp.headers.get('Location')!r})"
    )


@pytest.mark.deployed_pr("DataSpaceFrontend#525", site="HOME_URL_DEV")
def test_usecase_canonical_slug_serves_without_redirecting(
    dev_frontend_client, usecase_with_distinct_slug
):
    resp = dev_frontend_client.get(
        f"/usecases/{usecase_with_distinct_slug['urlSlug']}", allow_redirects=False
    )
    assert resp.status_code == 200, (
        f"canonical use case url /usecases/{usecase_with_distinct_slug['urlSlug']} "
        f"did not serve directly, got {resp.status_code} "
        f"(Location: {resp.headers.get('Location')!r})"
    )
