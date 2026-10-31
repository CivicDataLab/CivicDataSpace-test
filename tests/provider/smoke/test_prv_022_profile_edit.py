# tests/provider/smoke/test_prv_022_profile_edit.py
#
# The profile pages (DataSpaceFrontend#506): every editable field is changed,
# saved, and read back after a reload from the backend. The originals are read
# through the API first and written back by the `cleanup` fixture whatever the
# outcome. Not touched: the profile picture / organization logo (a saved image
# cannot be removed, only replaced), the e-mail (read-only) and the
# organization's name (renaming changes its slug and breaks the other tests).
#
# Run the individual case and the org case with the account that owns them
# (TEST_USER_INDEX), e.g. `-k individual` / `-k org`.

import uuid

import pytest

scopes = pytest.mark.parametrize(
    "scope",
    [pytest.param("individual", marks=pytest.mark.smoke), "org"],
)


def _new_values(scope, tag):
    """Values to type into every editable field, all different from what is there."""
    social = {
        "githubProfile": f"https://github.com/zz-auto-{tag}",
        "linkedinProfile": f"https://www.linkedin.com/in/zz-auto-{tag}",
        "twitterProfile": f"https://x.com/zz-auto-{tag}",
    }
    if scope == "individual":
        return {
            "firstName": f"zz-auto {tag}",
            "lastName": f"profile {tag}",
            "location": f"Zz Auto City {tag}",
            "bio": f"zz-auto bio {tag}",
            **social,
        }
    return {
        "homepage": f"https://zz-auto-{tag}.example.org",
        "location": f"Zz Auto City {tag}",
        "description": f"zz-auto description {tag}",
        **social,
    }


@pytest.mark.functional
@scopes
def test_prv_022_profile_edit_persists(scope, open_profile, provider_api, cleanup, request):
    """
    Test Case ID: test_prv_022_profile_edit_persists
    Every editable profile field keeps its new value after Save and a reload.
    Steps:
      1. Remember the current profile (restored when the test ends)
      2. Open the profile page and type a new value into each field; the org
         also picks a different Organization Type
      3. Save, reload, and read every field back
    """
    org = request.getfixturevalue("writable_org") if scope == "org" else None
    cleanup.restore_profile(org)

    page = open_profile(scope)
    tag = uuid.uuid4().hex[:8]
    values = _new_values(scope, tag)
    for name, value in values.items():
        page.enter_field(name, value)

    chosen_type = None
    if scope == "org":
        current = page.org_type()
        chosen_type = next(t for t in page.org_type_options() if t != current)
        page.choose_org_type(chosen_type)

    page.click_save()
    page.reload()

    assert {name: page.field_value(name) for name in values} == values, "Fields differ after Save and reload"
    if chosen_type:
        assert page.org_type() == chosen_type, "Organization Type was not saved"
    assert not page.field_enabled("email"), "The e-mail field should be read-only"


@pytest.mark.functional
@pytest.mark.xfail(
    strict=True,
    reason="Exploration issue I-3: the Change password button is hard-coded disabled, so it never leads to Keycloak",
)
def test_prv_023_change_password_opens_keycloak_account(open_profile, driver):
    """
    Test Case ID: test_prv_023_change_password_opens_keycloak_account
    The Change password button is enabled and takes a signed-in user to
    Keycloak's account page.
    Steps:
      1. Open the individual profile page
      2. The Change password button is enabled
      3. Clicking it lands on the Keycloak account page
    """
    import os
    from urllib.parse import urlparse

    page = open_profile("individual")
    assert page.change_password_enabled(), "The Change password button is disabled"
    page.click_change_password()
    keycloak_host = urlparse(os.environ["KEYCLOAK_URL"]).netloc
    page.wait_with_timeout(30).until(
        lambda d: urlparse(d.current_url).netloc == keycloak_host and "/account" in d.current_url,
        message="Change password did not lead to the Keycloak account page",
    )
