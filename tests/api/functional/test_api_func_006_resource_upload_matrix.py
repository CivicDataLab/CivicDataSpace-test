# tests/api/functional/test_api_func_006_resource_upload_matrix.py
#
# Upload edge cases for createFileResources. A file is accepted only when its
# extension and its sniffed type map to the same format (CSV, JSON, PDF, XLS(X),
# XML, ZIP). Covers each accepted format, disguised and unsupported files,
# empty files, odd file names, and what a rejected upload leaves behind.
# XLSX is not generated here (no spreadsheet library in requirements).

import io
import json
import zipfile

import pytest
import requests

from tests.api.client import _request_with_retries
from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

UPLOAD = """mutation($i: CreateFileResourceInput!){ createFileResources(fileResourceInput:$i){
  id name fileDetails { format } } }"""
RESOURCES = "query($id: UUID!){ datasetResources(datasetId:$id){ id name } }"

CSV = b"state,year,value\nAssam,2024,1\nBihar,2024,2\n"
PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
       b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6300010000050001")
EXE = b"MZ" + b"\x90\x00" * 64 + b"This program cannot be run in DOS mode.\r\n"


def _zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.csv", CSV.decode())
    return buf.getvalue()


@pytest.fixture
def dataset(graphql_client):
    body = gql(graphql_client, "mutation{ addDataset(createInput:{datasetType: DATA}){ data { id } } }")
    dataset_id = body["data"]["addDataset"]["data"]["id"]
    yield dataset_id
    gql(graphql_client, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": dataset_id})


@pytest.fixture
def upload(api_base_url, auth_token):
    def _do(dataset_id, filename, content):
        operations = {"query": UPLOAD, "variables": {"i": {"dataset": dataset_id, "files": [None]}}}
        resp = _request_with_retries(
            requests.post, f"{api_base_url.rstrip('/')}/api/graphql",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={"operations": json.dumps(operations), "map": json.dumps({"0": ["variables.i.files.0"]})},
            files={"0": (filename, content)},
        )
        assert resp.status_code == 200, resp.text[:300]
        return resp.json()
    return _do


@pytest.mark.parametrize("filename,content,fmt", [
    ("data.csv", CSV, "CSV"),
    ("data.json", b'[{"state":"Assam","value":1}]', "JSON"),
    ("report.pdf", PDF, "PDF"),
    ("feed.xml", b'<?xml version="1.0"?><rows><row state="Assam"/></rows>', "XML"),
    ("bundle.zip", _zip(), "ZIP"),
    ("DATA.CSV", CSV, "CSV"),
], ids=["csv", "json", "pdf", "xml", "zip", "upper-ext"])
def test_supported_format_is_accepted(graphql_client, dataset, upload, filename, content, fmt):
    body = upload(dataset, filename, content)
    assert "errors" not in body, body
    assert body["data"]["createFileResources"][0]["fileDetails"]["format"] == fmt


@pytest.mark.parametrize("filename,content", [
    ("image.png", PNG),
    ("tool.exe", EXE),
    ("disguised.csv", EXE),
    ("disguised.pdf", CSV),
    ("page.html", b"<html><body>hi</body></html>"),
    ("noextension", CSV),
], ids=["png", "exe", "exe-as-csv", "csv-as-pdf", "html", "no-extension"])
def test_unsupported_or_disguised_file_is_refused(dataset, upload, filename, content):
    body = upload(dataset, filename, content)
    assert any("Unsupported file format" in e["message"] for e in body.get("errors") or []), body


@pytest.mark.xfail(strict=True, reason="createFileResources creates the Resource before validating, so a rejected file leaves an orphan")
def test_refused_upload_leaves_no_resource(graphql_client, dataset, upload):
    upload(dataset, "tool.exe", EXE)
    assert gql(graphql_client, RESOURCES, {"id": dataset})["data"]["datasetResources"] == []


def test_empty_csv_is_handled(graphql_client, dataset, upload):
    body = upload(dataset, "empty.csv", b"")
    # Either refused cleanly or accepted as an empty resource, never a server crash.
    assert "errors" in body or body["data"]["createFileResources"], body
    assert not any("Internal" in e["message"] or "Traceback" in e["message"] for e in body.get("errors") or []), body


@pytest.mark.parametrize("filename", ["जनगणना डेटा.csv", "data (final) v2.csv", "a" * 150 + ".csv"],
                         ids=["devanagari", "spaces-parens", "long-150"])
def test_file_name_round_trips(graphql_client, dataset, upload, filename):
    body = upload(dataset, filename, CSV)
    assert "errors" not in body, body
    assert body["data"]["createFileResources"][0]["name"] == filename


def test_multiple_files_in_one_request(api_base_url, auth_token, graphql_client, dataset):
    operations = {"query": UPLOAD, "variables": {"i": {"dataset": dataset, "files": [None, None]}}}
    resp = _request_with_retries(
        requests.post, f"{api_base_url.rstrip('/')}/api/graphql",
        headers={"Authorization": f"Bearer {auth_token}"},
        data={"operations": json.dumps(operations),
              "map": json.dumps({"0": ["variables.i.files.0"], "1": ["variables.i.files.1"]})},
        files={"0": ("one.csv", CSV), "1": ("two.json", b'{"a":1}')},
    )
    body = resp.json()
    assert "errors" not in body, body
    assert sorted(r["name"] for r in body["data"]["createFileResources"]) == ["one.csv", "two.json"]
