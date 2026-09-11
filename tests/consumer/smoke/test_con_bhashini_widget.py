# tests/consumer/smoke/test_con_bhashini_widget.py
#
# Bhashini translation widget smoke coverage (DataSpaceFrontend PR #442).
#
# The widget is injected client-side by next/script with strategy
# "afterInteractive", so it does NOT appear in the server-rendered HTML —
# a requests-based check would always see it missing. It needs a real
# browser, hence the Selenium `driver` fixture.
#
# Scope, deliberately: only OUR integration points are asserted — the
# injected script tag, the container we render, and the mount holder. The
# widget's own rendered contents (language list, dropdown options, labels)
# are produced by translation-plugin.bhashini.co.in, a third party we don't
# control; on dev the container's innerText is in fact empty. Asserting on
# any of that would be flaky by construction.

import os

import pytest

from pages.consumer.bhashini_page import BhashiniWidgetPage

pytestmark = [pytest.mark.smoke, pytest.mark.readonly]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

PLUGIN_HOST = "translation-plugin.bhashini.co.in"


@pytest.fixture
def bhashini_home(driver):
    """Homepage loaded, wrapped in the Bhashini widget page object."""
    driver.get(BASE_URL)
    return BhashiniWidgetPage(driver)


def test_bhashini_plugin_script_is_injected(bhashini_home):
    """The third-party plugin bundle must be injected into the live DOM."""
    assert bhashini_home.has_plugin_script_by_src(), (
        f"No script[src*='{PLUGIN_HOST}'] found on {BASE_URL} — the Bhashini "
        "widget script was not injected"
    )
    src = bhashini_home.plugin_script_src()
    assert PLUGIN_HOST in src, (
        f"Injected script src does not point at the Bhashini plugin host: {src!r}"
    )


def test_bhashini_plugin_script_has_expected_id(bhashini_home):
    """
    next/script renders the tag with id 'bhashini-website-translation'.
    The id is what keeps the script from being injected twice across
    client-side navigations, so it is worth pinning.
    """
    assert bhashini_home.has_plugin_script_by_id(), (
        "No script with id 'bhashini-website-translation' found on "
        f"{BASE_URL} — the widget's next/script id changed or the script "
        "is not rendered"
    )


def test_bhashini_plugin_container_is_rendered(bhashini_home):
    """
    Our own .bhashini-plugin-container must be in the DOM.

    Presence only — its innerText is empty on dev because the third-party
    bundle had not populated it, and that is outside our control.
    """
    assert bhashini_home.has_plugin_container(), (
        f"No .bhashini-plugin-container found on {BASE_URL} — the widget "
        "container is not being rendered"
    )


def test_bhashini_plugin_holder_is_rendered(bhashini_home):
    """The #__bhashini-plugin-holder mount point must exist for the bundle."""
    assert bhashini_home.has_plugin_holder(), (
        f"No #__bhashini-plugin-holder found on {BASE_URL} — the plugin has "
        "no element to mount into"
    )
