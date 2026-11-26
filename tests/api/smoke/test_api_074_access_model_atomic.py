# tests/api/smoke/test_api_074_access_model_atomic.py
#
# DataSpaceBackend#316 (fix #320): createAccessModel and editAccessModel save
# nothing when a request is refused. Before the fix a refused create left an
# empty access model on the dataset, a refused edit deleted the model's existing
# resource links first, and an edit without an id left an empty new model.
# "Another dataset's file" on create is covered by test_api_064.
#
# The control (a valid edit still saves) is what makes the "nothing changed"
# checks mean something.

import uuid

import pytest

from tests.api.smoke.test_api_064_dataset_parts_permissions import (
    ACCESS_MODEL, OWNER, _account, _data, _new_dataset, _upload,
)

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#320")]

NO_SUCH_FIELD = 999999999
EDIT = "mutation($i: EditAccessModelInput!){ editAccessModel(accessModelInput:$i){ __typename } }"
MODELS = "query($d: UUID!){ accessModelResources(datasetId:$d){ id } }"
STATE = """query($a: UUID!){ accessModel(accessModelId:$a){
  id name description type resourceFields { resource { id } fields } } }"""


@pytest.fixture(scope="module")
def world():
    owner = _account(OWNER)
    a, b = _new_dataset(owner), _new_dataset(owner)
    try:
        yield owner, {"a": a, "b": b,
                      "file_a": _upload(owner, a, f"qa-{uuid.uuid4().hex[:8]}.csv"),
                      "file_b": _upload(owner, b, f"qa-{uuid.uuid4().hex[:8]}.csv")}
    finally:
        for d in (a, b):
            owner.gql("mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": d})


@pytest.fixture
def model(world):
    """A fresh access model on dataset A holding A's file."""
    owner, ids = world
    created = _data(owner.gql(ACCESS_MODEL, {"i": {"dataset": ids["a"], "name": "[qa] kept", "description": "qa",
                                                   "type": "PRIVATE", "resources": [{"resource": ids["file_a"], "fields": []}]}}),
                    "createAccessModel")
    yield created["id"]
    owner.gql("mutation($a: UUID!){ deleteAccessModel(accessModelId:$a) }", {"a": created["id"]})


def _refused(body):
    if body.get("errors"):
        assert "__init__" not in str(body["errors"]), f"The request was malformed, not refused: {body['errors']}"
        return True
    data = next(iter(body["data"].values()))
    return data["__typename"] != "TypeAccessModel"


def _state(owner, model_id):
    return _data(owner.gql(STATE, {"a": model_id}), "accessModel")


def _model_ids(owner, dataset):
    return sorted(m["id"] for m in _data(owner.gql(MODELS, {"d": dataset}), "accessModelResources"))


def _edit(owner, ids, model_id, **changes):
    """editAccessModel needs every field; a request missing one fails for that reason, not the one under test."""
    full = {"dataset": ids["a"], "accessModelId": model_id, "name": "[qa] kept", "description": "qa", "type": "PRIVATE",
            "resources": [{"resource": ids["file_a"], "fields": []}], **changes}
    return owner.gql(EDIT, {"i": full})


def test_a_valid_edit_still_saves(world, model):
    owner, ids = world
    body = _edit(owner, ids, model, name="[qa] renamed")
    assert not _refused(body), f"A valid edit was refused: {body}"
    assert _state(owner, model)["name"] == "[qa] renamed"


def test_create_with_an_unknown_field_saves_no_access_model(world, model):
    owner, ids = world
    body = owner.gql(ACCESS_MODEL, {"i": {"dataset": ids["a"], "name": "[qa] bad field", "description": "qa", "type": "PRIVATE",
                                          "resources": [{"resource": ids["file_a"], "fields": [NO_SUCH_FIELD]}]}})
    assert _refused(body), f"A field that does not exist was accepted: {body}"
    assert _model_ids(owner, ids["a"]) == [model], "A refused create left an access model behind"


def test_edit_with_another_datasets_file_keeps_name_and_resources(world, model):
    owner, ids = world
    before = _state(owner, model)
    body = _edit(owner, ids, model, name="[qa] changed", resources=[{"resource": ids["file_b"], "fields": []}])
    assert _refused(body), f"An edit took another dataset's file: {body}"
    assert _state(owner, model) == before, "A refused edit changed the access model"


def test_edit_with_an_unknown_field_keeps_the_resources(world, model):
    owner, ids = world
    before = _state(owner, model)
    body = _edit(owner, ids, model, resources=[{"resource": ids["file_a"], "fields": [NO_SUCH_FIELD]}])
    assert _refused(body), f"A field that does not exist was accepted: {body}"
    assert _state(owner, model) == before, "A refused edit dropped the access model's resources"


def test_refused_edit_without_an_id_saves_no_access_model(world, model):
    owner, ids = world
    body = _edit(owner, ids, None, name="[qa] new", resources=[{"resource": ids["file_b"], "fields": []}])
    assert _refused(body), f"An edit took another dataset's file: {body}"
    assert _model_ids(owner, ids["a"]) == [model], "A refused edit without an id left an access model behind"
