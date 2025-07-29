# tests/conftest.py

import os
from dotenv import load_dotenv
import sys
import subprocess
# load environment variables from the .env file in the project root
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

from _pytest.runner import runtestprotocol
from pathlib import Path
import logging
import tempfile
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Imports to get firefox driver working
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


# This global dict will map each failed test nodeid → its screenshot relative path.
#
FAILED_SCREENSHOTS = {}

def pytest_configure(config):
    # this will always print once at startup
    print("\n🐍 root conftest.py: pytest_configure loaded")

# ─── LOGGER SETUP ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

logging.getLogger("WDM").setLevel(logging.WARNING)
# optionally prevent it from propagating to the root logger:
logging.getLogger("WDM").propagate = False


def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="run browser with GUI instead of headless"
    )
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Send 'chrome' or 'firefox' as parameter for execution"
    )

# ─── SELENIUM DRIVER FIXTURE ────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def driver(request):
    """
    Launch a headless Chrome on GitHub Actions (Ubuntu). We force Chrome to use
    a brand-new, empty user-data directory (in /tmp) on each session so that
    “user data directory already in use” errors never occur.
    """
    browser = request.config.getoption("--browser")
    drv = ""
    # 1) Build ChromeOptions
    opts = webdriver.ChromeOptions()

    caps = DesiredCapabilities.CHROME.copy()
    caps["goog:loggingPrefs"] = {"performance": "ALL"}

    # Use the new headless mode; on GH runners this avoids some legacy issues.
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--window-size=1920,1080")
    # optionally start maximized
    opts.add_argument("--start-maximized")

    # 2) Create a fresh, empty directory for Chrome's user-data
    tmp_dir = tempfile.mkdtemp(prefix="chrome-user-data-")
    opts.add_argument(f"--user-data-dir={tmp_dir}")

    opts.set_capability("goog:loggingPrefs", caps["goog:loggingPrefs"])

    # 3) Install the matching chromedriver, then start Chrome
    if browser == "chrome":
        drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    elif browser == "firefox":
        drv = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))

    # Implicit wait setup for our framework
    drv.implicitly_wait(3)
    # also turn on the CDP Network domain so we can grab bodies
    drv.execute_cdp_cmd("Network.enable", {})
    yield drv

    # 4) Teardown: quit Chrome and remove the temp folder
    try:
        print("quitting driver")
        drv.quit()
    except Exception:
        pass
    # Clean up the temp profile directory
    try:
        # shutil.rmtree would remove it recursively
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

@pytest.fixture(scope="session")
def base_url():
    """
    This fixture should return the URL that your HomePage.load() does:
       driver.get(HOME_URL_DEV)
    """
    url = os.getenv("HOME_URL_DEV")  # ← local .env probably sets this
    if not url:
        pytest.skip("HOME_URL_DEV is not set")
    return url

#  ─────────────────────── Sample csv file fixture ─────────────────────────────
@pytest.fixture(scope="session")
def sample_csv_path():
    data_file = Path(__file__).parent / "tests" / "data" / "sample_create.csv"
    if not data_file.exists():
        raise FileNotFoundError(f"Expected sample_create.csv at {data_file}")
    return str(data_file)

@pytest.fixture()
def sample_logo_path():
    """
    Returns an absolute path to a small image under tests/data/
    so that CreateUsecasePage.upload_logo(...) can send_keys() it.
    """
    here = os.path.dirname(__file__)    # this is a string
    logo_path = os.path.abspath(os.path.join(here, "tests", "data", "sample_logo.png"))
    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Expected sample_logo.png at {logo_path}")
    return logo_path


# 1) pytest_runtest_makereport
#    After each test “call” phase, if it failed and a WebDriver fixture is present,
#    take a screenshot and stash (nodeid → relative PNG path) in FAILED_SCREENSHOTS.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Called after each test run phase. If the test “call” phase failed and the test
    has a WebDriver fixture, take a screenshot and record the relative path in FAILED_SCREENSHOTS.
    """
    outcome = yield
    rep = outcome.get_result()

    # We only care about failures in the “call” phase
    if rep.when == "call" and rep.failed:
        # 1) See if any fixture in this test is a WebDriver instance
        driver_obj = None
        for _, fixture_val in item.funcargs.items():
            if isinstance(fixture_val, WebDriver):
                driver_obj = fixture_val
                break

        if not driver_obj:
            # No WebDriver fixture → nothing to screenshot
            return

        # 2) Make sure ./screenshots exists
        screenshots_dir = Path(os.getcwd()) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # 3) Build a filename from the test nodeid
        sanitized = item.name
        png_path = screenshots_dir / f"{sanitized}.png"

        try:
            driver_obj.save_screenshot(str(png_path))
            rel = os.path.relpath(str(png_path), os.getcwd())

            # Record in the global dict for pytest_json_modifyreport to inject later
            FAILED_SCREENSHOTS[rep.nodeid] = rel

            print(f"\n📸 [HOOK] Saved screenshot for {rep.nodeid}: {rel}\n")
        except Exception as e:
            print(f"\n⚠️ [HOOK] Could not save screenshot for {rep.nodeid}: {e}\n")


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 2) pytest_json_modifyreport
#    This hook is provided by pytest-json-report. It runs after the plugin builds its
#    internal JSON data but before writing report.json. We inject our screenshot path here.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.hookimpl
def pytest_json_modifyreport(json_report):
    """
    For each test in the JSON report, if we have a screenshot recorded in FAILED_SCREENSHOTS,
    append ["screenshot", <rel_path>] into that test’s "user_properties" array.
    """
    for test_dict in json_report.get("tests", []):
        nodeid = test_dict.get("nodeid")
        if nodeid in FAILED_SCREENSHOTS:
            rel_path = FAILED_SCREENSHOTS[nodeid]
            if "user_properties" not in test_dict or test_dict["user_properties"] is None:
                test_dict["user_properties"] = []
            test_dict["user_properties"].append(["screenshot", rel_path])
            print(f"🔗 [HOOK] Injected screenshot into JSON for {nodeid}: {rel_path}")


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 3) pytest_sessionfinish
#    After pytest finishes running all tests (and after report.json is written),
#    automatically call report_generator.py to produce TEST_REPORT.md and TEST_REPORT.pdf.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """
    Called once pytest is completely done. If report.json exists, invoke report_generator.py.
    """
    rpt = Path(os.getcwd()) / "report.json"
    if rpt.exists():
        print("\n\n📄 Generating TEST_REPORT.md + TEST_REPORT.pdf …")
        subprocess.run([sys.executable, "report_generator.py"], check=False)
    else:
        print("\n\n⚠️  report.json not found; skipping report generation.")