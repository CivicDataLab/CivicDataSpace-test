# tests/api/smoke/test_api_038_metadata_export_formats.py
#
# Covers the parts of DataSpaceBackend#211 (per-dataset metadata export) that
# test_api_018 leaves out: the RDF serialisations, the Croissant and Dublin
# Core documents, the post-processing the exporter applies on top of the
# crosswalk (typed dates, IANA media-type IRIs, licence on every distribution,
# Croissant FileObject fields), the format/standard matrix and `report=1`.
#
# Unauthenticated and read-only, so readonly-safe; gated like test_api_018.
#
# Not covered: draft datasets visible to their owner, and the 500 branch.

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceBackend#211"),
]

XSD_DATE = "http://www.w3.org/2001/XMLSchema#date"
IANA_BASE = "https://www.iana.org/assignments/media-types/"
CROISSANT_CONFORMS_TO = "http://mlcommons.org/croissant/1.1"


@pytest.fixture(scope="module")
def dataset_id(anon_graphql_client):
    """A published dataset that has resources, read live."""
    rows = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 20}) { id resources { id } } }"
    )["datasets"]
    found = next((r["id"] for r in rows if r["resources"]), None)
    if not found:
        pytest.skip("no published dataset with resources on this backend to export")
    return found


@pytest.fixture(scope="module")
def export(anon_api_client, dataset_id):
    """GET the export once per (standard, format, extra params) and reuse it."""
    cache = {}

    def get(standard, fmt="jsonld", **extra):
        key = (standard, fmt, tuple(sorted(extra.items())))
        if key not in cache:
            cache[key] = anon_api_client.get(
                f"/api/datasets/{dataset_id}/export/",
                params={"standard": standard, "format": fmt, **extra},
            )
        return cache[key]

    return get


# (standard, format, content type, file extension, marker the body must contain)
SERIALISATIONS = [
    ("dcat", "turtle", "text/turtle", "ttl", "@prefix"),
    ("dcat", "rdfxml", "application/rdf+xml", "rdf", "<rdf:RDF"),
    ("dcat", "ntriples", "application/n-triples", "nt", "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"),
    ("dublin_core", "turtle", "text/turtle", "ttl", "@prefix"),
    ("croissant", "jsonld", "application/ld+json", "jsonld", '"@type"'),
]


@pytest.mark.smoke
@pytest.mark.parametrize(
    "standard,fmt,content_type,ext,marker",
    SERIALISATIONS,
    ids=[f"{s}-{f}" for s, f, *_ in SERIALISATIONS],
)
def test_export_serialisation_matches_requested_format(
    export, dataset_id, standard, fmt, content_type, ext, marker
):
    """Each standard/format pair returns that syntax, with the matching download headers."""
    resp = export(standard, fmt)
    assert resp.status_code == 200, f"{standard}/{fmt}: {resp.status_code}: {resp.text[:300]}"
    assert resp.headers.get("Content-Type", "").startswith(content_type), resp.headers.get("Content-Type")
    disposition = resp.headers.get("Content-Disposition", "")
    assert disposition.startswith("attachment;") and disposition.rstrip('"').endswith(f".{standard}.{ext}"), disposition
    assert marker in resp.text, f"{standard}/{fmt} body is not {fmt}: {resp.text[:200]!r}"
    assert dataset_id in resp.text, f"{standard}/{fmt} body does not carry the dataset id"


@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parametrize(
    "standard,fmt",
    [("croissant", "turtle"), ("dcat", "not_a_real_format")],
    ids=["croissant-is-jsonld-only", "unknown-format"],
)
def test_export_rejects_a_format_the_standard_does_not_offer(export, standard, fmt):
    """Croissant is JSON-LD only and unknown formats are rejected: 400, never a 500 or a file."""
    resp = export(standard, fmt)
    assert resp.status_code == 400, f"{standard}/{fmt}: {resp.status_code}: {resp.text[:300]}"
    assert "json" in resp.headers.get("Content-Type", ""), resp.headers.get("Content-Type")
    assert "error" in resp.json(), resp.text
    assert "Content-Disposition" not in resp.headers


@pytest.mark.smoke
@pytest.mark.regression
def test_dcat_export_applies_typed_dates_iana_media_types_and_distribution_licence(export):
    """The exporter's DCAT-AP fix-ups run: xsd:date literals, IANA IRIs, licence per distribution."""
    doc = export("dcat", "jsonld").json()

    dates = [doc[p] for p in ("dcterms:issued", "dcterms:modified", "dcterms:created") if p in doc]
    assert dates, f"export has no date properties to check: {sorted(doc)}"
    for value in dates:
        assert isinstance(value, dict) and value.get("@type") == XSD_DATE, (
            f"date must be an xsd:date literal, got {value!r}"
        )

    dists = doc.get("dcat:distribution") or []
    assert dists, "dataset with resources exported no distributions"
    media_types = [d["dcat:mediaType"] for d in dists if "dcat:mediaType" in d]
    assert media_types, f"no distribution carries a media type: {dists}"
    for mt in media_types:
        assert isinstance(mt, dict) and mt.get("@id", "").startswith(IANA_BASE), (
            f"media type must be an IANA IRI, got {mt!r}"
        )

    if "dcterms:license" in doc:
        for dist in dists:
            assert dist.get("dcterms:license") == doc["dcterms:license"], dist


@pytest.mark.smoke
@pytest.mark.regression
def test_croissant_export_declares_conformance_and_complete_file_objects(export, dataset_id):
    """Croissant requires conformsTo, and an @id, contentUrl and encodingFormat on each FileObject."""
    doc = export("croissant", "jsonld").json()
    assert doc.get("conformsTo") == CROISSANT_CONFORMS_TO, doc.get("conformsTo")
    assert doc.get("identifier") == dataset_id, doc.get("identifier")

    files = doc.get("distribution") or []
    assert files, "dataset with resources exported no FileObjects"
    for f in files:
        missing = [k for k in ("@id", "contentUrl", "encodingFormat") if not f.get(k)]
        assert not missing, f"FileObject lacks {missing}: {f}"


@pytest.mark.smoke
@pytest.mark.regression
def test_dublin_core_export_is_a_dcterms_document_for_this_dataset(export, dataset_id):
    """The Dublin Core standard yields a dcterms:Dataset, not the DCAT or Croissant shape."""
    doc = export("dublin_core", "jsonld").json()
    assert doc.get("@type") == "dcterms:Dataset", doc.get("@type")
    assert doc.get("dcterms:identifier") == dataset_id, doc.get("dcterms:identifier")
    assert doc.get("dcterms:title"), doc
    assert "dcat:distribution" not in doc and "distribution" not in doc, sorted(doc)


@pytest.mark.smoke
@pytest.mark.regression
def test_export_report_mode_returns_the_gap_report_beside_the_document(export, dataset_id):
    """`report=1` swaps the file download for JSON: {standard, format, report, document}."""
    resp = export("dcat", "jsonld", report="1")
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:300]}"
    assert "Content-Disposition" not in resp.headers
    body = resp.json()
    assert set(body) == {"standard", "format", "report", "document"}, sorted(body)
    assert (body["standard"], body["format"]) == ("dcat", "jsonld")
    assert {"dropped", "unresolved", "missing_mandatory"} <= set(body["report"]), sorted(body["report"])
    assert body["document"].get("dcterms:identifier") == dataset_id, body["document"]
