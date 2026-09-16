"""Pill getters must read their own field, not the first tag pill on the page."""
import pytest

from locators.provider.create_usecase_locators import CreateUsecaseLocators
from locators.provider.create_collaborative_locators import CreateCollaborativeLocators
from locators.provider.create_dataset_locators import CreateDatasetLocators

pytestmark = pytest.mark.regression

PILLS = [
    (CreateUsecaseLocators, ["SELECTED_TAGS", "SELECTED_SECTORS", "SELECTED_GEOGRAPHY", "SELECTED_SDG_GOALS"]),
    (CreateCollaborativeLocators, ["SELECTED_TAGS", "SELECTED_SECTORS", "SELECTED_GEOGRAPHY", "SELECTED_SDG_GOALS"]),
    (CreateDatasetLocators, ["SECTOR_SELECTED_PILL", "TAG_SELECTED_PILL", "GEOGRAPHY_SELECTED_PILL"]),
]


@pytest.mark.parametrize("cls,name", [(c, n) for c, names in PILLS for n in names])
def test_pill_locator_is_scoped_to_its_own_field(cls, name):
    xpath = getattr(cls, name)
    assert xpath.startswith("//label["), f"{cls.__name__}.{name} is not anchored on its label"
    assert "ancestor::div[.//input[@role='combobox']][1]" in xpath, (
        f"{cls.__name__}.{name} is not scoped to its own field wrapper"
    )
