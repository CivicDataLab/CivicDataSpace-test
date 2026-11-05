# tests/api/smoke/test_api_012_publishers_jsonld.py
#
# Regression coverage for DataSpaceFrontend#443 (the /publishers part of it).
#
# The /publishers listing page emits a schema.org JSON-LD block for search
# engines. Its `name` and `description` were read from
# `getPublishers.title` / `.description`, but getPublishers returns a LIST, so
# both were undefined and JSON.stringify dropped them. The block shipped with
# no name or description from the start. #443 sets both explicitly.
#
# The block is server-rendered, so a plain GET sees it; no browser needed.

import json
import re

import pytest

pytestmark = pytest.mark.readonly

LD_JSON_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S
)


def _ld_json_objects(html):
    objects = []
    for block in LD_JSON_RE.findall(html):
        data = json.loads(block)
        objects.extend(data if isinstance(data, list) else [data])
    return objects


@pytest.mark.api
@pytest.mark.seo
@pytest.mark.smoke
def test_publishers_jsonld_has_name_and_description(dev_frontend_client, frontend_base_url_dev):
    url = f"{frontend_base_url_dev}/publishers"
    resp = dev_frontend_client.get(
        "/publishers",
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"},
    )
    assert resp.status_code == 200, f"GET {url} returned {resp.status_code}"

    blocks = [o for o in _ld_json_objects(resp.text) if str(o.get("url", "")).rstrip("/").endswith("/publishers")]
    assert len(blocks) == 1, (
        f"Expected one JSON-LD block for {url}, found {len(blocks)} "
        f"among {[o.get('@type') for o in _ld_json_objects(resp.text)]}"
    )
    block = blocks[0]
    for field in ("name", "description"):
        value = block.get(field)
        assert isinstance(value, str) and value.strip(), (
            f"{url} JSON-LD is missing '{field}' (got {value!r}); keys present: {sorted(block)}"
        )
