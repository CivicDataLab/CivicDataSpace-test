import os
import shutil
import pytest
from datetime import datetime

from pages.home_page import HomePage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.organizations_page import OrganizationsPage
from pages.provider.create_dataset_page import CreateDatasetPage


@pytest.mark.functional
def test_prv_006b_org_create_prompt_dataset(driver, sample_csv_path, base_url, test_credentials):
    """
    Test Case ID: test_prv_006b_org_create_prompt_dataset
    Verify a user can create a Prompt Dataset end-to-end from the Org Dashboard.
    Steps:
      1. Access Homepage and log in
      2. Navigate to Organizations dashboard and select an org
      3. Click "Add New Dataset" → select "Prompt Dataset"
      4. Fill Metadata (Description, Sectors, Tags, Geography, Date, Source, License)
      5. Fill Prompt-specific Metadata (Task Type, Domain, Target Languages, Target Model Types)
      6. Upload a prompt file (Prompt Files tab)
      7. Publish and verify Published status
    """
    driver.delete_all_cookies()

    home = HomePage(driver, base_url)
    email, password = test_credentials
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load"
    except Exception:
        pass

    # Step 1: Login
    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), (
        "test_prv_006b: go_to_login(flow='provider') did not return ProviderHomePage"
    )

    # Step 2: Go to Org Dashboard and select org
    org_dash = prov_home.goto_organizations()
    assert isinstance(org_dash, OrganizationsPage), (
        "test_prv_006b: goto_organizations() did not return OrganizationsPage"
    )

    select_org = org_dash.select_org()
    assert isinstance(select_org, OrganizationsPage), (
        "test_prv_006b: select_org() did not return OrganizationsPage"
    )

    # Step 3: Create a Prompt Dataset
    create_ds = org_dash.click_add_new_prompt_dataset()
    assert isinstance(create_ds, CreateDatasetPage), (
        "test_prv_006b: click_add_new_prompt_dataset() did not return CreateDatasetPage"
    )

    # ── Step 4: METADATA TAB ──────────────────────────────────────────────────

    create_ds.go_to_metadata_tab()

    # 4a) Description
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_description = f"Automated org prompt dataset test {timestamp}"
    create_ds.enter_description(test_description)
    actual_desc = create_ds.get_description_value()
    assert actual_desc == test_description, (
        f"Step 4a: Expected description '{test_description}', got '{actual_desc}'"
    )

    # 4b) Sectors
    create_ds.select_sectors(["Budgets"])
    assert "Budgets" in create_ds.get_selected_sectors(), (
        "Step 4b: Sector 'Budgets' was not selected"
    )

    # 4c) Tags
    create_ds.select_tags(["Finance"])
    assert "Finance" in create_ds.get_selected_tags(), (
        "Step 4c: Tag 'Finance' was not selected"
    )

    # 4d) Geography
    create_ds.select_geography("Assam")
    assert "Assam" in create_ds.get_selected_geography(), (
        "Step 4d: Geography 'Assam' was not selected"
    )

    # 4e) Date of Creation
    create_ds.enter_date_created("09022021")
    actual_date = create_ds.get_date_created_value()
    assert actual_date in ("2021-09-02", "2021-02-09"), (
        f"Step 4e: Unexpected date value '{actual_date}'"
    )

    # 4f) Source Website
    create_ds.enter_source_website("https://example.com")
    assert create_ds.get_source_website_value() == "https://example.com", (
        "Step 4f: Source website not set correctly"
    )

    # 4g) License
    create_ds.select_license("CC BY 4.0 (Attribution)")
    assert create_ds.get_selected_license_text() == "CC BY 4.0 (Attribution)", (
        "Step 4g: License not set correctly"
    )

    # ── Step 5: PROMPT DATASET METADATA ──────────────────────────────────────

    # 5a) Task Type
    create_ds.select_task_type("QUESTION ANSWERING")
    task_type_pills = create_ds.get_selected_task_type()
    assert any("QUESTION ANSWERING" in v for v in task_type_pills), (
        f"Step 5a: Task Type 'QUESTION ANSWERING' not found in pills: {task_type_pills}"
    )

    # 5b) Domain
    create_ds.select_domain("GOVERNMENT")
    domain_pills = create_ds.get_selected_domain()
    assert any("GOVERNMENT" in v for v in domain_pills), (
        f"Step 5b: Domain 'GOVERNMENT' not found in pills: {domain_pills}"
    )

    # 5c) Target Languages
    create_ds.select_target_languages(["HINDI"])
    lang_pills = create_ds.get_selected_target_languages()
    assert any("HINDI" in v for v in lang_pills), (
        f"Step 5c: Target Language 'HINDI' not found in pills: {lang_pills}"
    )

    # 5d) Target Model Types
    create_ds.select_target_model_types(["GPT"])
    model_pills = create_ds.get_selected_target_model_types()
    assert any("GPT" in v for v in model_pills), (
        f"Step 5d: Target Model Type 'GPT' not found in pills: {model_pills}"
    )

    # ── Step 6: PROMPT FILES TAB ──────────────────────────────────────────────

    create_ds.go_to_prompt_files_tab()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = os.path.basename(sample_csv_path)
    name, ext = os.path.splitext(original_filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    unique_path = os.path.join(os.path.dirname(sample_csv_path), unique_filename)
    shutil.copy2(sample_csv_path, unique_path)

    create_ds.upload_prompt_file(unique_path)

    uploaded = create_ds.get_uploaded_resource_names()
    assert unique_filename in uploaded, (
        f"Step 6: '{unique_filename}' not found in uploaded files: {uploaded}"
    )

    try:
        os.remove(unique_path)
    except Exception:
        pass

    # ── Step 7: PUBLISH ───────────────────────────────────────────────────────

    detail_page = create_ds.go_to_publish_tab()
    assert detail_page.is_publish_tab_visible(), (
        "Step 7: Publish tab did not become visible"
    )

    detail_page.click_publish()

    assert detail_page.is_published(), (
        "Step 7: Dataset was not marked as Published after clicking Publish"
    )
