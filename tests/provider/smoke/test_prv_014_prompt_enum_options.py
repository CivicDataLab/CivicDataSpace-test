import pytest

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.create_dataset_page import CreateDatasetPage

# Prompt dropdown label -> the backend GraphQL enum it is built from.
METADATA_DROPDOWNS = {
    "Task Type": "PromptTaskType",
    "Domain": "PromptDomain",
    "Target Languages": "TargetLanguage",
    "Target Model Types": "TargetModelType",
}


def _assert_same_options(label, enum_name, actual, expected):
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    assert sorted(actual) == expected, (
        f"'{label}' options differ from backend enum {enum_name}: "
        f"missing {missing}, unexpected {extra}"
    )


@pytest.mark.regression
def test_prv_014_prompt_dropdowns_list_every_backend_value(
    driver, sample_csv_path, base_url, test_credentials, backend_enum_labels
):
    """
    Test Case ID: test_prv_014_prompt_dropdowns_list_every_backend_value
    Every prompt dataset dropdown offers exactly the backend enum's values.

    DataSpaceFrontend#465 moved these options from runtime introspection to enums
    compiled in at build time. A frontend built against an older schema would
    silently drop new values; one whose options fail to load shows none. Both fail
    here.
      1. Log in, open My Dashboard, add a Prompt Dataset
      2. Metadata tab: Task Type, Domain, Target Languages, Target Model Types
      3. Prompt Files tab: upload a file, then Prompt Format on its edit view
    """
    driver.delete_all_cookies()
    home = HomePage(driver, base_url)
    email, password = test_credentials
    if not home.is_loaded():
        home.load()

    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), "Login did not reach ProviderHomePage"
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), "Could not open My Dashboard"
    create_ds = my_dash.click_add_new_prompt_dataset()
    assert isinstance(create_ds, CreateDatasetPage), "Could not start a Prompt Dataset"

    create_ds.go_to_metadata_tab()
    for label, enum_name in METADATA_DROPDOWNS.items():
        _assert_same_options(
            label, enum_name,
            create_ds.get_prompt_field_options(label), backend_enum_labels(enum_name),
        )

    create_ds.go_to_prompt_files_tab()
    create_ds.upload_prompt_file_and_open(sample_csv_path)
    _assert_same_options(
        "Prompt Format", "PromptFormat",
        create_ds.get_prompt_field_options("Prompt Format"), backend_enum_labels("PromptFormat"),
    )
