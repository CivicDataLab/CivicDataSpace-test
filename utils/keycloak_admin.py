# utils/keycloak_admin.py
#
# Thin Keycloak Admin API client, used only so registration tests can delete
# the accounts they create.
#
# The governing rule for anything in this file: never create an account we
# cannot delete. Tests that register a user must skip outright when admin
# access is unavailable, rather than leaving strays in the realm. `available()`
# exists for exactly that check.
#
# Auth is the `dataspace` client's service account (client_credentials). It has
# manage-users on the realm but not much else - listing identity providers, for
# instance, returns 403 - so keep this to user lifecycle operations.

import os

import requests

TIMEOUT = 20


class KeycloakAdmin:
    def __init__(self, base_url=None, realm=None, client_id=None, client_secret=None):
        self.base_url = (base_url or os.getenv("KEYCLOAK_URL", "")).rstrip("/")
        self.realm = realm or os.getenv("KEYCLOAK_REALM", "")
        self.client_id = client_id or os.getenv("KEYCLOAK_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("KEYCLOAK_CLIENT_SECRET", "")
        self._token = None

    def available(self):
        """True only if a service-account token can actually be obtained.

        Checked before creating anything, so a missing or unprivileged secret
        turns into a skip instead of an undeletable test account.
        """
        if not all([self.base_url, self.realm, self.client_id, self.client_secret]):
            return False
        try:
            return self._get_token() is not None
        except requests.RequestException:
            return False

    def _get_token(self):
        if self._token:
            return self._token
        resp = requests.post(
            f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        self._token = resp.json().get("access_token")
        return self._token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def find_users_by_email(self, email):
        """Exact-match lookup. Returns [] when the user does not exist."""
        resp = requests.get(
            f"{self.base_url}/admin/realms/{self.realm}/users",
            headers=self._headers(),
            params={"email": email, "exact": "true"},
            timeout=TIMEOUT,
        )
        return resp.json() if resp.status_code == 200 else []

    def user_exists(self, email):
        return len(self.find_users_by_email(email)) > 0

    def delete_user_by_email(self, email):
        """Delete every user matching the email. Returns how many were removed.

        Safe to call for an email that was never created - registration may
        have been rejected, which is the expected path in the consent test.
        """
        deleted = 0
        for user in self.find_users_by_email(email):
            resp = requests.delete(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user['id']}",
                headers=self._headers(),
                timeout=TIMEOUT,
            )
            if resp.status_code in (204, 200):
                deleted += 1
        return deleted
