# tests/consumer/functional/test_con_func_304_published_aimodel.py
#
# A public AI model shows its provider's values on /aimodels/<id>, is found by
# /search, and disappears when made private. The last test flips it private,
# so it must stay last.

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from tests.api.publications import gql

pytestmark = [pytest.mark.functional]


@pytest.fixture
def page(driver):
    return PublishedItemPage(driver)


def _detail(page, base_url, m):
    return page.open_detail(base_url, "aimodel", m["id"], m["title"])


def test_detail_shows_provider_values(page, base_url, public_ai_model):
    m = public_ai_model
    text = _detail(page, base_url, m).text()
    for value in (m["title"], m["description"], m["tag"], "Summarisation", "Agriculture", m["geography"]["name"]):
        assert value in text, f"{value!r} missing from AI model detail"


@pytest.mark.xfail(strict=True, reason="New public AI models never reach /search on dev (same symptom as DataSpaceBackend#290)")
def test_search_finds_public_model(page, base_url, public_ai_model):
    assert page.listing_shows(base_url, "search", public_ai_model["title"], types="aimodel", query=public_ai_model["tag"])


def test_private_model_detail_is_gone(page, base_url, graphql_client, public_ai_model):
    m = public_ai_model
    gql(graphql_client, "mutation($i: UpdateAIModelInput!){ updateAiModel(input:$i){ success } }",
        {"i": {"id": m["id"], "isPublic": False}})
    _detail(page, base_url, m)
    assert page.is_not_found() and m["description"] not in page.text(), "private AI model still served"
