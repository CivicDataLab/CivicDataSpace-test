# pages/consumer/share_panel.py
from locators.consumer.share_locators import ShareLocators as L
from pages.base_page import BasePage


class SharePanel(BasePage):
    """The share actions on a public page. Open the panel first where it sits in a popover."""

    def open_dataset_popover(self):
        self.click(L.DATASET_TRIGGER)
        self.find(L.COPY)
        return self

    def links(self):
        """{aria-label: {href, target, rel}} for the X, LinkedIn, Facebook and email links."""
        anchors = self.finds(L.LINKS)
        return {
            a.get_attribute("aria-label"): {
                "href": a.get_attribute("href"),
                "target": a.get_attribute("target"),
                "rel": a.get_attribute("rel"),
            }
            for a in anchors
        }

    def copy_link(self):
        """Click Copy link and return the status line once it settles on something."""
        self.click(L.COPY)
        return self.wait.until(lambda d: (d.find_element(*L.STATUS).get_attribute("textContent") or "").strip())

    def copy_control_reads_copied(self):
        return self.find(L.COPIED).is_displayed()
