# tests/provider/functional/test_prv_005_ind_edit_profile.py
import pytest
from pages.home_page import HomePage
from pages.provider.login_page import LoginPage
from pages.provider.provider_home_page import ProviderHomePage
from pages.provider.my_dashboard_page import MyDashboardPage
from pages.provider.update_profile_page import UpdateProfilePage




@pytest.mark.smoke
def test_prv_005_ind_edit_profile(driver, sample_csv_path, base_url, test_credentials):
    """
        Test Case ID: test_prv_005_ind_edit_profile
        Verify User is able to edit profile details.
        Steps:
          1. Access Homepage
          2. Click LOGIN / SIGN UP and log in
          3. Navigate to “My Dashboard”
          4. Under Left navigation pane, select Profile section
          5. Fill in First name, Last name, Github profile, Linkedin Profile, Location, Twitter profile, Bio,
          6. Upload a profile picture
          7. Click on Save button
          9. Assert the profile details are updated
        """

    driver.delete_all_cookies()
    # Step 1: load homepage
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
        "test_prv_005: expected HomePage.go_to_login(flow='provider') to return ProviderHomePage"
    )

    # Step 3: In the “ProviderHomePage” (the /dashboard screen), click “My Dashboard”
    my_dash = prov_home.goto_my_dashboard()
    assert isinstance(my_dash, MyDashboardPage), (
        "test_prv_005: expected ProviderHomePage.goto_my_dashboard() to return MyDashboardPage"
    )

    # Step 4: Within MyDashboardPage, click “Profile”:
    up_profile = my_dash.click_profile_card()
    assert up_profile.is_loaded(), "My Profile page did not load properly"
    assert isinstance(up_profile, UpdateProfilePage), (
        "test_prv_002: expected click_profile_card() to return UpdateProfilePage"
    )

    # ─── Step 5: My Profile Page ──────────────────────────────────────────────────────────────────────

    # (5a) First Name

    first_name = "Saqib"
    up_profile.enter_first_name(first_name)
    get_first_name = up_profile.get_first_name_value()
    assert get_first_name == first_name, (
        f"Step 5a failure: Expected first name to be '{first_name}', but found '{get_first_name}'."
    )