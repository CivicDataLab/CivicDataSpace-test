# locators/consumer/collaboratives_locators.py

from selenium.webdriver.common.by import By


class CollaborativesLocators:
    """XPaths for elements on the public Collaboratives listing page."""

    @staticmethod
    def img_with_src(src: str):
        """Any <img> whose resolved src attribute exactly matches *src*."""
        return (By.XPATH, f"//img[@src={_xpath_literal(src)}]")


def _xpath_literal(value: str) -> str:
    """Quote *value* safely for use inside an XPath expression, even if it
    contains a single quote. Media URLs here are percent-encoded, so this is
    a belt-and-braces guard rather than an expected case."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"
