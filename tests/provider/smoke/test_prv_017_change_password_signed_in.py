# tests/provider/smoke/test_prv_017_change_password_signed_in.py
#
# Profile "Change password" (DataSpaceFrontend#534): the button calls
# signIn('keycloak', ..., {kc_action: 'UPDATE_PASSWORD'}), so a signed-in user
# lands straight on Keycloak's update-password form. The form is only opened,
# never submitted: no password is changed.

import os
from urllib.parse import urlparse

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceFrontend#534", site="HOME_URL_DEV")]


def test_prv_017_change_password_opens_keycloak_form(open_profile):
    page = open_profile("individual")
    assert page.change_password_enabled(), "The Change password button is disabled"
    page.click_change_password()
    page.wait_for_keycloak_update_password(urlparse(os.environ["KEYCLOAK_URL"]).netloc)
