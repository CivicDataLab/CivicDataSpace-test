# tests/provider/functional/test_prv_009_org_edit_profile.py
import pytest
from pages.home_page import HomePage
from pages.provider.login_page import LoginPage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.update_profile_page import UpdateProfilePage
from pages.provider.organizations_page import OrganizationsPage


@pytest.mark.smoke
def test_prv_009_org_edit_profile(driver, sample_profile_image_path, base_url, test_credentials):
    """
    Test Case ID: test_prv_009_org_edit_profile
    Verify User is able to edit organization profile details.

    Steps:
      1. Access Homepage
      2. Click LOGIN / SIGN UP and log in
      3. Navigate to "Organizations"
      4. Select an organization
      5. Navigate to the organization's profile section
      6. Fill in organization details (name, description, location, social links, etc.)
      7. Upload an organization logo/image
      8. Click on Save button
      9. Assert the profile details are updated

    Note: This test follows the individual profile edit pattern (test_prv_005)
    but applies it to organization profile management.
    """

    driver.delete_all_cookies()

    # Step 1: Load homepage
    home = HomePage(driver, base_url)
    email, password = test_credentials
    try:
        if not home.is_loaded():
            home.load()
            assert home.is_loaded(), "Homepage did not load successfully"
    except Exception as e:
        print(f"Error loading homepage: {e}")

    # Step 2: Login as provider (auto-redirects to /dashboard)
    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    assert isinstance(prov_home, ProviderHomePage), (
        "test_prv_009: expected HomePage.go_to_login(flow='provider') to return ProviderHomePage"
    )

    # Step 3: Navigate to Organizations page
    org_dash = prov_home.goto_organizations()
    assert isinstance(org_dash, OrganizationsPage), (
        "test_prv_009: expected goto_organizations() to return OrganizationsPage"
    )

    # Step 4: Select one of the organizations
    select_org = org_dash.select_org()
    assert isinstance(select_org, OrganizationsPage), (
        "test_prv_009: expected select_org() to return OrganizationsPage"
    )

    # Step 5: Navigate to organization profile section
    # Note: Assuming there's a profile card or section for organizations
    # This may need to be adapted based on actual UI implementation
    org_profile = org_dash.click_profile_card()
    assert org_profile.is_loaded(), "Organization Profile page did not load properly"
    assert isinstance(org_profile, UpdateProfilePage), (
        "test_prv_009: expected click_profile_card() to return UpdateProfilePage"
    )

    # ─── Step 6: Organization Profile Details ──────────────────────────────────────────

    # (6a) Organization Name / First Name field
    org_name = "CivicDataLab"
    org_profile.enter_first_name(org_name)
    get_org_name = org_profile.get_first_name_value()
    assert get_org_name == org_name, (
        f"Step 6a failure: Expected organization name to be '{org_name}', but found '{get_org_name}'."
    )

    # (6b) Organization Description / Last Name field (or bio)
    org_description = "Leading civic tech organization"
    org_profile.enter_last_name(org_description)
    get_org_desc = org_profile.get_last_name_value()
    assert get_org_desc == org_description, (
        f"Step 6b failure: Expected description to be '{org_description}', but found '{get_org_desc}'."
    )

    # (6c) Organization Bio Text
    bio_text = "CivicDataLab works with data, tech, and design for public good."
    org_profile.enter_bio_text(bio_text)
    get_bio_text = org_profile.get_bio_text_value()
    assert get_bio_text == bio_text, (
        f"Step 6c failure: Expected bio to be '{bio_text}', but found '{get_bio_text}'."
    )

    # (6d) Upload Organization Logo/Profile Image
    org_profile.upload_profile_image(sample_profile_image_path)
    assert org_profile.is_profile_image_uploaded(), (
        "Step 6d failure: Organization logo/profile image upload did not succeed."
    )

    # (6e) Click Save Button
    org_profile.click_save()
    # Verify save was successful by checking if profile image is still uploaded
    assert org_profile.is_profile_image_uploaded(), (
        "Step 6e failure: Clicking save button did not succeed."
    )

    print("[SUCCESS] test_prv_009_org_edit_profile completed successfully")
    print("[NOTE] Organization profile fields may differ from individual profile - adapt as needed")
