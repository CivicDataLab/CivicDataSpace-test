# tests/api/smoke/test_api_033_usecase_meta_description.py
#
# DataSpaceFrontend#470 changed what a use case's `summary` holds: the new
# content editor saves a JSON document ({"version":1,"subtitle":...,"blocks":[...]})
# instead of HTML. The public /usecases/<id> page's <meta name="description">
# and og:description were the raw summary, so they now go through
# getUseCaseSummaryExcerpt: plain text, at most 180 chars plus "…", and the
# subtitle for a JSON summary.
#
# Before #470 (still prod's behaviour when this was written) use case 311's
# description was its 5317-char HTML summary, tags included. A JSON summary
# would have shipped as raw JSON.
#
# Server-rendered metadata, so a plain GET sees it. `readonly` + `deployed_pr`:
# skips on any site whose X-Git-Sha doesn't include #470 yet.

import html
import json
import re

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.seo,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceFrontend#470", site="HOME_URL_DEV"),
]

EXCERPT_LIMIT = 180
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"}
META_RE = re.compile(r'<meta\b[^>]*\b(?:name|property)="(description|og:description)"[^>]*>')
CONTENT_RE = re.compile(r'\bcontent="([^"]*)"')


# Mirrors the frontend's plainTextFromHtml, which decodes only these entities.
_ENTITIES = [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")]


def _plain(text):
    text = re.sub(r"<[\s\S]*?>", " ", text)
    for entity, char in _ENTITIES:
        text = re.sub(re.escape(entity), char, text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def _excerpt(text):
    return text if len(text) <= EXCERPT_LIMIT else text[:EXCERPT_LIMIT].rstrip() + "\u2026"


def _json_subtitle(summary):
    try:
        doc = json.loads(summary)
    except ValueError:
        return None
    if isinstance(doc, dict) and doc.get("version") == 1 and isinstance(doc.get("subtitle"), str):
        return doc["subtitle"].strip() or None
    return None


@pytest.fixture(scope="module")
def published_use_cases(anon_graphql_client):
    return anon_graphql_client.query("{ publishedUseCases { id summary } }")["publishedUseCases"]


def _pick(use_cases, kind):
    for uc in use_cases:
        summary = uc.get("summary") or ""
        if kind == "json" and _json_subtitle(summary):
            return uc
        # Legacy HTML long enough that the excerpt must strip tags AND truncate.
        if kind == "html" and summary.lstrip().startswith("<") and len(_plain(summary)) > EXCERPT_LIMIT:
            return uc
    pytest.skip(f"no published use case with a {kind} summary on this environment")


@pytest.mark.parametrize("kind", ["html", "json"])
def test_usecase_meta_description_is_plain_excerpt(kind, published_use_cases, dev_frontend_client):
    uc = _pick(published_use_cases, kind)
    summary = uc["summary"]
    path = f"/usecases/{uc['id']}"
    resp = dev_frontend_client.get(path, headers=UA)
    assert resp.status_code == 200, f"GET {path} returned {resp.status_code}"

    metas = {m.group(1): html.unescape(CONTENT_RE.search(m.group(0)).group(1)) for m in META_RE.finditer(resp.text)}
    assert set(metas) == {"description", "og:description"}, f"{path} meta tags found: {sorted(metas)}"

    expected = _excerpt(_json_subtitle(summary) if kind == "json" else _plain(summary))

    for name, value in metas.items():
        assert value == expected, (
            f"{path} {name} should be the {kind} summary's plain excerpt.\n"
            f"expected ({len(expected)}): {expected[:120]!r}\n"
            f"got      ({len(value)}): {value[:120]!r}"
        )
