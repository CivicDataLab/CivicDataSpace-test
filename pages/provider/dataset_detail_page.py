from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class DatasetDetailPage(BasePage):
    def is_published(self) -> bool:
        return "Published" in self.find((By.XPATH, "//span[contains(@class,'StatusBadge')]")).text

    def get_download_url(self) -> str:
        link = self.find((By.XPATH, "//a[normalize-space()='Download']"))
        return link.get_attribute("href")
