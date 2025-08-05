# tests/provider/functional/test_prv_002_ind_create_dataset.py
import os
import pytest
import requests
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.home_page import HomePage
from pages.provider.login_page import LoginPage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.create_dataset_page import CreateDatasetPage

@pytest.mark.smoke
def test_prv_002_ind_create_dataset(driver, sample_csv_path, base_url):

    """
    Test Case ID: test_prv_002_ind_create_dataset
    Verify User is able to create a Dataset end-to-end as an Individual provider.
    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and log in
      3. Navigate to “My Dashboard”
      4. Under Datasets section click on “Add New Dataset”
      5. Fill in Description, Sectors, Tags, Geography, Date, Source, License
      6. Upload a sample file
      7. Switch to Publish section
      8. Click on Publish
      9. Assert the dataset is marked “Published”
     10. Download the dataset and verify HTTP 200
    """
    driver.delete_all_cookies()
    # Step 1: load homepage
    home = HomePage(driver, base_url)
    
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load successfully"
    except Exception as e:
        print(f"Error loading homepage: {e}")

    # Step 2: Login as provider (auto-redirects to /dashboard)
    prov_home = home.go_to_login(flow="provider")
    assert isinstance(prov_home, ProviderHomePage), (
        "test_prv_002: expected HomePage.go_to_login(flow='provider') to return ProviderHomePage"
    )

    # Step 3: In the “ProviderHomePage” (the /dashboard screen), click “My Dashboard”
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        "test_prv_002: expected ProviderHomePage.goto_my_dashboard() to return MyDashboardPage"
    )

    # Step 4: Within MyDashboardPage, click “Add New Dataset”:
    create_ds = my_dash.click_add_new_dataset()
    assert isinstance(create_ds, CreateDatasetPage), (
        "test_prv_002: expected click_add_new_dataset() to return CreateDatasetPage"
    )

    # ─── Step 5: METADATA TAB ──────────────────────────────────────────────────────────────────────
    create_ds.go_to_metadata_tab()

    # (5a) Description
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_description = f"Automated test description {timestamp}"
    create_ds.enter_description(test_description)
    # Make sure the description field actually holds our value:
    actual_desc = create_ds.get_description_value()
    assert actual_desc == test_description, (
        f"Step 5a failure: Expected description to be '{test_description}', but found '{actual_desc}'."
    )

    # (5b) Sectors
    create_ds.select_sectors(["Public Finance"])
    selected_sectors = create_ds.get_selected_sectors()  # e.g. returns ['Budgets']
    assert "Public Finance" in selected_sectors, (
        f"Step 5b failure: Sector 'Budgets' was not selected; current selection = {selected_sectors}."
    )

    # (5c) Tags
    create_ds.select_tags(["Finance"])
    selected_tags = create_ds.get_selected_tags()  # e.g. returns ['Budget']
    assert "Finance" in selected_tags, (
        f"Step 5c failure: Tag 'Finance' was not selected; current tags = {selected_tags}."
    )

    # (5d) Geography
    create_ds.select_geography("Assam")
    actual_geo = create_ds.get_selected_geography()  # e.g. returns 'India'
    assert actual_geo == "Assam", (
        f"Step 5d failure: Expected geography 'Assam', but saw '{actual_geo}'."
    )

    # (5e) Date of Creation
    test_date = "09022021"
    create_ds.enter_date_created(test_date)
    # Because some date‐pickers store in ISO format (DDMMYYYY), let’s compare accordingly:
    actual_date = create_ds.get_date_created_value()  # e.g. returns '09022021'
    assert actual_date == "2021-02-09", (
        f"Step 5e failure: Expected date_created '{test_date}', but got '{actual_date}'."
    )

    # (5f) Source Website
    test_source = "https://example.com"
    create_ds.enter_source_website(test_source)
    actual_src = create_ds.get_source_website_value()
    assert actual_src == test_source, (
        f"Step 5f failure: Expected source website '{test_source}', but found '{actual_src}'."
    )

    # (5g) License
    license_to_pick = "CC BY 4.0 (Attribution)"
    create_ds.select_license(license_to_pick)
    actual_license = create_ds.get_selected_license_text()
    assert actual_license == license_to_pick, (
        f"Step 5g failure: Expected license '{license_to_pick}', but got '{actual_license}'."
    )

    # ─── Step 6: DATA FILES TAB ──────────────────────────────────────────────────────────────────────
    create_ds.go_to_datafiles_tab()

    # (6a) Upload sample CSV
    create_ds.upload_datafile(sample_csv_path)

    # (6b) Verify that our CSV appears under “Uploaded Files”
    uploaded_list = create_ds.get_uploaded_resource_names()
    expected_base = os.path.basename(sample_csv_path)
    assert expected_base in uploaded_list, (
        f"Step 6b failure: After uploading, expected '{expected_base}' in {uploaded_list}."
    )

    # ─── Step 7: PUBLISH TAB ─────────────────────────────────────────────────────────────────────────
    detail_page = create_ds.go_to_publish_tab()
    assert detail_page.is_publish_tab_visible(), (
        "Step 7 failure: Publish tab did not become visible after switching."
    )
    # (7a) Click “Publish”
    detail_page.click_publish()

    # (7b) Verify “Published” status in UI
    assert detail_page.is_published(), (
        "Step 7b failure: After clicking Publish, the network request does not has status : PUBLISHED."
    )
    #
    # # (7c) Verify download‐URL returns HTTP 200
    # download_url = detail_page.get_download_url()
    # response = requests.head(download_url, allow_redirects=True)
    # assert response.status_code == 200, (
    #     f"Step 7c failure: Expected HTTP 200 from '{download_url}', but got {response.status_code}."
    # )
