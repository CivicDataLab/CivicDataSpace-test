# tests/consumer/smoke/test_con_usecase_rich_text_sanitization.py
#
# DataSpaceFrontend#566: the use case story body (the `summary` field) is
# rendered through sanitizeRichText before it reaches the page, so markup the
# rich-text editor itself cannot produce no longer reaches the DOM.
#
# A throwaway published use case carries the check: its summary is set once to
# a fixed mix of formatting the editor *can* produce (kept) and markup it
# cannot (removed), and the public detail page is read back.

import uuid

import pytest

from pages.consumer.usecase_page import UseCasePage
from tests.api.publications import gql
from tests.api.publish_ready import make_use_case_publishable

pytestmark = [pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceFrontend#566", site="HOME_URL_DEV")]

ADD = "mutation{ addUseCase { ... on TypeUseCase { id } ... on OperationInfo { messages { message } } } }"
PUBLISH = "mutation($i: String!){ publishUseCase(useCaseId:$i){ ... on TypeUseCase { status } ... on OperationInfo { messages { message } } } }"
DELETE = "mutation($i: String!){ deleteUseCase(useCaseId:$i) }"
UPDATE_SUMMARY = "mutation($d: UseCaseInputPartial!){ updateUseCase(data:$d){ id } }"
STORED_SUMMARY = "query($pk: ID!){ useCase(pk:$pk){ summary } }"

# A mix the rich-text editor can produce (kept by the allow-list in
# lib/sanitizeRichText.ts) and markup it cannot (must not reach the DOM).
MARKER = uuid.uuid4().hex[:8]
SAFE_HTML = f"<p>qa-{MARKER} safe <b>bold</b> and <i>italic</i> text.</p>"
UNSAFE_SCRIPT = f"<script>window.__qa_{MARKER}__ = 1;</script>"
UNSAFE_EVENT_HANDLER = f'<img src="x" onerror="window.__qa_{MARKER}__ = 1">'
UNSAFE_SCHEME_LINK = f'<a href="javascript:window.__qa_{MARKER}__=1" id="qa-{MARKER}-link">click</a>'
SUMMARY_HTML = SAFE_HTML + UNSAFE_SCRIPT + UNSAFE_EVENT_HANDLER + UNSAFE_SCHEME_LINK


@pytest.fixture(scope="module")
def sanitized_usecase(graphql_client):
    body = gql(graphql_client, ADD)
    assert not body.get("errors"), body
    uc_id = body["data"]["addUseCase"]["id"]
    try:
        make_use_case_publishable(graphql_client, uc_id)
        body = gql(graphql_client, UPDATE_SUMMARY, {"d": {"id": uc_id, "summary": SUMMARY_HTML}})
        assert not body.get("errors"), body
        # The frontend's sanitizer is what's under test, so the backend must still store the markup.
        stored = gql(graphql_client, STORED_SUMMARY, {"pk": uc_id})["data"]["useCase"]["summary"]
        if not all(part in stored for part in ("<script", "onerror", "javascript:")):
            pytest.skip(f"the backend now strips the unsafe markup itself ({stored!r}), so the page can't show the frontend's sanitizer")
        body = gql(graphql_client, PUBLISH, {"i": uc_id})
        assert not body.get("errors") and body["data"]["publishUseCase"].get("status") == "PUBLISHED", body
        yield uc_id
    finally:
        gql(graphql_client, DELETE, {"i": uc_id})


@pytest.fixture
def uc_page(driver):
    return UseCasePage(driver, timeout=30)


@pytest.fixture
def story_html(sanitized_usecase, uc_page):
    import os

    base_url = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")
    uc_page.open_detail(base_url, sanitized_usecase)
    return uc_page.story_body_html()


def test_rich_text_keeps_formatting_the_editor_can_produce(story_html):
    assert f"qa-{MARKER} safe" in story_html, story_html
    assert "<b>bold</b>" in story_html, story_html
    assert "<i>italic</i>" in story_html, story_html


def test_rich_text_strips_script_tags(story_html):
    assert "<script" not in story_html.lower(), story_html


def test_rich_text_strips_event_handler_attributes(story_html):
    assert "onerror" not in story_html.lower(), story_html


def test_rich_text_strips_unsupported_url_schemes(story_html):
    assert "javascript:" not in story_html.lower(), story_html
