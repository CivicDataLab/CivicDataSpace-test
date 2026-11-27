# tests/api/smoke/test_api_078_publication_jsonld_escape.py
#
# DataSpaceFrontend#566: generateJsonLd escapes "<" as <. The publication
# detail page renders its JSON-LD on the server with the raw description, so
# before the fix a description containing "</script>" closed the JSON-LD block
# early and the rest of it was parsed as page HTML.
#
# A throwaway published publication carries a harmless breakout: a <b> with a
# unique id. The server-rendered HTML must not contain that element, every
# JSON-LD block must still parse, and the description must come back whole.

import json
import re
import uuid

import pytest

from tests.api import publications as pub

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.deployed_pr("DataSpaceFrontend#566", site="HOME_URL_DEV"),
]

LD_JSON_RE = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
MARKER = uuid.uuid4().hex[:8]
# No quotes: JSON would escape them, and the check below looks for the tag as written.
BREAKOUT = f"</script><b id=qa-{MARKER}>x</b>"
DESCRIPTION = f"qa-{MARKER} {BREAKOUT}"


@pytest.fixture(scope="module")
def published_slug(graphql_client_for):
    owner = graphql_client_for(1)
    data = pub.create(owner, **pub.complete_fields(owner))
    try:
        payload = pub.update(owner, data["id"], description=DESCRIPTION)
        assert payload["success"], payload["errors"]
        stored = pub.get(owner, data["id"])["data"]["getPublication"]["description"]
        if "</script>" not in stored:
            pytest.skip(f"the backend no longer stores '</script>' in a description ({stored!r}), nothing reaches the JSON-LD")
        payload = pub.publish(owner, data["id"])
        assert payload["success"], payload["errors"]
        body = pub.gql(owner, "query($id: UUID!){ getPublication(publicationId:$id){ urlSlug } }", {"id": data["id"]})
        yield body["data"]["getPublication"]["urlSlug"]
    finally:
        pub.delete(owner, data["id"])


def test_description_cannot_close_the_jsonld_block(published_slug, dev_frontend_client):
    resp = dev_frontend_client.get(f"/en/publications/{published_slug}")
    assert resp.status_code == 200, f"/en/publications/{published_slug} returned {resp.status_code}"
    html = resp.text

    assert f"<b id=qa-{MARKER}>" not in html, "the description closed the JSON-LD script and its HTML reached the page"

    objects = [json.loads(block) for block in LD_JSON_RE.findall(html)]
    ours = [o for o in objects if f"qa-{MARKER}" in str(o.get("description", ""))]
    assert ours, f"no JSON-LD block carries the description; blocks: {[o.get('@type') for o in objects]}"
    assert ours[0]["description"] == DESCRIPTION, ours[0]["description"]
