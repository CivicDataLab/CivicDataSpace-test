# tests/api/smoke/test_api_016_publication_blocks.py
#
# Publication content blocks (DataSpace#243): YouTube and file blocks, their
# validation, rename / reorder / remove / replace, and that a draft's file
# can't be downloaded anonymously. Writes to dev only; drafts are deleted in
# teardown, which also removes their files.

import pytest
import requests

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.functional]

VIDEO_ID = "dQw4w9WgXcQ"


@pytest.fixture
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture
def draft(owner):
    data = pub.create(owner, title=pub.unique_title("blocks test"))
    yield data["id"]
    pub.delete(owner, data["id"])


@pytest.mark.parametrize("url", [
    f"https://www.youtube.com/watch?v={VIDEO_ID}",
    f"https://youtu.be/{VIDEO_ID}",
    f"https://www.youtube.com/embed/{VIDEO_ID}",
    f"https://www.youtube.com/shorts/{VIDEO_ID}",
], ids=["watch", "short_link", "embed", "shorts"])
def test_youtube_link_shapes_are_accepted(owner, draft, url):
    payload = pub.add_youtube(owner, draft, url)
    assert payload["success"], payload["errors"]
    assert payload["data"]["youtubeVideoId"] == VIDEO_ID, payload["data"]


def test_non_youtube_link_is_rejected(owner, draft):
    payload = pub.add_youtube(owner, draft, "https://vimeo.com/123456")
    assert not payload["success"], payload
    assert pub.errors_of(payload) == {None: ["Enter a valid YouTube video URL."]}, payload["errors"]
    assert pub.blocks(owner, draft) == []


@pytest.mark.smoke
def test_pdf_block_is_titled_after_its_file(owner, draft):
    payload = pub.add_file(owner, draft, "quarterly report.pdf", pub.PDF_BYTES)
    assert payload["success"], payload["errors"]
    assert payload["data"]["blockType"] == "FILE", payload["data"]
    assert payload["data"]["title"] == "quarterly report", payload["data"]


@pytest.mark.parametrize("file_name, content, message", [
    ("fake.pdf", b"not a pdf", "File claims to be a PDF but its contents are not."),
    ("tool.exe", b"MZ", "is not an allowed file type"),
], ids=["fake_pdf", "exe"])
def test_disallowed_files_are_rejected(owner, draft, file_name, content, message):
    payload = pub.add_file(owner, draft, file_name, content)
    assert not payload["success"], payload
    assert any(message in m for m in pub.errors_of(payload).get(None, [])), payload["errors"]
    assert pub.blocks(owner, draft) == []


def test_renaming_a_block_keeps_its_description(owner, draft):
    block = pub.add_youtube(owner, draft, f"https://youtu.be/{VIDEO_ID}", title="Talk", description="Keynote")["data"]
    payload = pub.mutate(
        owner, "updatePublicationBlock",
        "mutation($b: UUID!){ updatePublicationBlock(blockId:$b, title:\"Renamed\"){ %s data { title description } } }" % pub.RESULT,
        {"b": block["id"]},
    )
    assert payload["success"], payload["errors"]
    assert payload["data"] == {"title": "Renamed", "description": "Keynote"}


def test_reorder_must_list_every_block_once(owner, draft):
    ids = [pub.add_youtube(owner, draft, f"https://youtu.be/{VIDEO_ID}", title=str(n))["data"]["id"] for n in range(3)]
    reorder = (
        "mutation($id: UUID!, $b: [UUID!]!){ reorderPublicationBlocks(publicationId:$id, blockIds:$b){ %s } }" % pub.RESULT
    )

    partial = pub.mutate(owner, "reorderPublicationBlocks", reorder, {"id": draft, "b": ids[:2]})
    assert pub.errors_of(partial) == {None: ["Reorder must list every block exactly once."]}, partial

    full = pub.mutate(owner, "reorderPublicationBlocks", reorder, {"id": draft, "b": ids[::-1]})
    assert full["success"], full["errors"]
    assert [b["title"] for b in pub.blocks(owner, draft)] == ["2", "1", "0"]


def test_removing_a_block_renumbers_the_rest(owner, draft):
    ids = [pub.add_youtube(owner, draft, f"https://youtu.be/{VIDEO_ID}", title=str(n))["data"]["id"] for n in range(3)]
    payload = pub.mutate(
        owner, "removePublicationBlock",
        "mutation($b: UUID!){ removePublicationBlock(blockId:$b){ %s } }" % pub.RESULT, {"b": ids[0]},
    )
    assert payload["success"], payload["errors"]
    assert [(b["position"], b["title"]) for b in pub.blocks(owner, draft)] == [(0, "1"), (1, "2")]


def test_only_file_blocks_can_be_replaced(owner, draft):
    block = pub.add_youtube(owner, draft, f"https://youtu.be/{VIDEO_ID}")["data"]
    payload = pub.upload(
        owner,
        "mutation($b: UUID!, $file: Upload!){ replacePublicationBlockFile(blockId:$b, file:$file){ %s } }" % pub.RESULT,
        {"b": block["id"]}, "new.pdf", pub.PDF_BYTES,
    )
    assert pub.errors_of(payload) == {None: ["Only a file block's file can be replaced."]}, payload


def test_draft_file_downloads_only_for_its_owner(owner, draft, api_base_url):
    block = pub.add_file(owner, draft, "private.pdf", pub.PDF_BYTES)["data"]
    url = f"{api_base_url}/api/publications/blocks/{block['id']}/download/"

    assert requests.get(url, timeout=30).status_code == 404, "anonymous download of a draft file"
    resp = owner.session.get(url, timeout=30)
    assert resp.status_code == 200, resp.status_code
    assert resp.content.startswith(b"%PDF"), resp.content[:20]
