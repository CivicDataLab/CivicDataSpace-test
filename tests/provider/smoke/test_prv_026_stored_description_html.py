# tests/provider/smoke/test_prv_026_stored_description_html.py
#
# HTML a provider puts in a description must be shown, not run, on the public
# page. Account 3 publishes an AI model whose description carries an image
# with an `onerror` handler that only sets a page global; an anonymous browser
# opens the public page and the global must stay unset. The model is deleted
# at teardown. Dev only (writes).

import os
import uuid

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.smoke, pytest.mark.security]

MARKER = "__storedHtmlRan"


@pytest.fixture
def public_model():
    if not (os.getenv("API_BASE_URL") and os.getenv("TEST_EMAIL_3") and os.getenv("TEST_PASSWORD_3")):
        pytest.skip("needs API_BASE_URL and TEST_EMAIL_3/TEST_PASSWORD_3")
    api = ProviderAPI(os.environ["TEST_EMAIL_3"], os.environ["TEST_PASSWORD_3"])
    title = f"zz-auto-html-{uuid.uuid4().hex[:8]}"
    body = api.gql(
        "mutation($i: CreateAIModelInput!){ createAiModel(input:$i){ success data { id } } }",
        {"i": {"modelType": "SUMMARIZATION", "provider": "CUSTOM", "name": title, "displayName": title,
               "domain": "AGRICULTURE", "isPublic": True,
               "description": f'<p>{title}</p><img src="x" onerror="window.{MARKER}=1">'}},
    )
    model_id = int(body["data"]["createAiModel"]["data"]["id"])
    try:
        api.gql("mutation($i: UpdateAIModelInput!){ updateAiModel(input:$i){ success } }",
                {"i": {"id": model_id, "status": "ACTIVE"}})
        yield {"id": model_id, "title": title}
    finally:
        api.delete("aimodel", model_id)


@pytest.mark.xfail(strict=True, reason="known product defect, tracked by the frontend team")
def test_description_html_is_not_run_on_the_public_page(driver, base_url, public_model):
    page = PublishedItemPage(driver).open_detail(base_url, "aimodel", public_model["id"], public_model["title"])
    assert public_model["title"] in page.text(), "the public AI model page did not show the model"
    assert page.page_value(MARKER) is None, "the description's onerror handler ran on the public AI model page"
