# tests/conftest.py

import os
from dotenv import load_dotenv
import sys
import subprocess
# load environment variables from the .env file in the project root
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

from _pytest.runner import runtestprotocol
from pathlib import Path
import platform
import shutil
import logging
import stat
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
from selenium.webdriver.chrome.service import Service as ChromeService
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
@pytest.fixture
def driver(request):
    browser = request.config.getoption("--browser", default="chrome").lower()

    # Common Chrome flags
    opts = webdriver.ChromeOptions()
    for flag in (
        "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", "--disable-extensions",
        "--window-size=1920,1080", "--start-maximized"
    ):
        opts.add_argument(flag)

    # Isolate user-data
    tmp_profile = tempfile.mkdtemp(prefix="chrome-user-data-")
    opts.add_argument(f"--user-data-dir={tmp_profile}")

    if browser == "chrome":
        # 1) Fetch via webdriver_manager
        raw_path = ChromeDriverManager().install()
        folder = os.path.dirname(raw_path)

        # 2) If the returned path isn't the actual binary, look for it
        if not os.access(raw_path, os.X_OK) or os.path.basename(raw_path) != "chromedriver":
            candidates = [
                fn for fn in os.listdir(folder)
                if fn.lower() == "chromedriver"
            ]
            if not candidates:
                raise RuntimeError(
                    f"Couldn’t find executable ‘chromedriver’ in {folder}. "
                    f"Files there: {os.listdir(folder)}"
                )
            real = os.path.join(folder, candidates[0])
            # ensure it’s executable
            st = os.stat(real)
            os.chmod(real, st.st_mode | stat.S_IXUSR)
            driver_path = real
        else:
            driver_path = raw_path

        print(f"[INFO] Using chromedriver at: {driver_path}")
        service = ChromeService(driver_path)
        drv = webdriver.Chrome(service=service, options=opts)

    elif browser == "firefox":
        gd = GeckoDriverManager().install()
        print(f"[INFO] Using geckodriver at: {gd}")
        service = FirefoxService(gd)
        drv = webdriver.Firefox(service=service)

    else:
        raise ValueError(f"Unsupported browser: {browser!r}")

    # Debug
    print(f"[INFO] session id: {drv.session_id}")
    print(f"[INFO] window handle: {drv.current_window_handle}")

    drv.implicitly_wait(3)
    try:
        drv.execute_cdp_cmd("Network.enable", {})
    except Exception:
        pass

    yield drv

    # Teardown
    try:
        drv.quit()
    except:
        pass
    shutil.rmtree(tmp_profile, ignore_errors=True)

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
    data_file = Path(__file__).parent / "tests" / "data" / "sam_create.csv"
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

@pytest.fixture(scope="session")
def test_credentials():
    """
        Reads TEST_USER_INDEX (1 or 2) from the environment,
        then returns (email, password) pulled from TEST_EMAIL_1/2 and TEST_PASSWORD_1/2.
        """
    idx = int(os.getenv("TEST_USER_INDEX", "1"))
    email = os.getenv(f"TEST_EMAIL_{idx}")
    password = os.getenv(f"TEST_PASSWORD_{idx}")
    assert email and password, f"Credentials for user index {idx} not set!"
    return email, password


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