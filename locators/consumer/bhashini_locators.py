# locators/consumer/bhashini_locators.py
#
# Selectors for the Bhashini translation widget integration.
#
# Only OUR integration points are located here — the injected <script>, the
# container we render for the plugin, and the holder the plugin mounts into.
# The widget's own rendered contents (language dropdown, buttons, labels)
# come from translation-plugin.bhashini.co.in, a third party we don't
# control, so nothing inside them is a stable test target.

from selenium.webdriver.common.by import By


class BhashiniLocators:
    # The third-party plugin bundle, injected client-side by next/script
    # (strategy "afterInteractive") — so it exists only in the live DOM,
    # never in the server-rendered HTML.
    SCRIPT_BY_SRC = (By.CSS_SELECTOR, 'script[src*="translation-plugin.bhashini.co.in"]')
    SCRIPT_BY_ID = (By.CSS_SELECTOR, "#bhashini-website-translation")

    # The element our own layout renders for the plugin to attach to.
    PLUGIN_CONTAINER = (By.CSS_SELECTOR, ".bhashini-plugin-container")

    # The mount point the plugin bundle looks for by id.
    PLUGIN_HOLDER = (By.CSS_SELECTOR, "#__bhashini-plugin-holder")
