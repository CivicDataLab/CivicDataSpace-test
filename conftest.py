# tests/conftest.py

import os
from dotenv import load_dotenv
import sys
import subprocess
# load environment variables from the .env file in the project root
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

from pathlib import Path
import shutil
import logging
import re
import stat
import tempfile
import pytest
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

# Imports to get firefox driver working
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


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

# ─── WEBDRIVER BINARY (resolved once per worker) ────────────────────────────────
@pytest.fixture(scope="session")
def webdriver_binary(request):
    """
    Absolute path to the chromedriver/geckodriver binary.

    webdriver-manager hits the network to check for a newer driver and writes to
    the shared ~/.wdm cache, so doing this per test cost a round-trip on every
    one of them and let parallel workers race on the same cache directory.
    Resolving once per session (i.e. once per xdist worker) keeps both problems
    to a single call.
    """
    browser = request.config.getoption("--browser", default="chrome").lower()

    if browser == "firefox":
        path = GeckoDriverManager().install()
        print(f"[INFO] Using geckodriver at: {path}")
        return path

    raw_path = ChromeDriverManager().install()
    folder = os.path.dirname(raw_path)

    # If the returned path isn't the actual binary, look for it
    if not os.access(raw_path, os.X_OK) or os.path.basename(raw_path) != "chromedriver":
        candidates = [fn for fn in os.listdir(folder) if fn.lower() == "chromedriver"]
        if not candidates:
            raise RuntimeError(
                f"Couldn’t find executable ‘chromedriver’ in {folder}. "
                f"Files there: {os.listdir(folder)}"
            )
        real = os.path.join(folder, candidates[0])
        # ensure it’s executable
        st = os.stat(real)
        os.chmod(real, st.st_mode | stat.S_IXUSR)
        raw_path = real

    print(f"[INFO] Using chromedriver at: {raw_path}")
    return raw_path


# ─── SELENIUM DRIVER FIXTURE ────────────────────────────────────────────────────
@pytest.fixture
def driver(request, webdriver_binary):
    browser = request.config.getoption("--browser", default="chrome").lower()

    # Common Chrome flags
    opts = webdriver.ChromeOptions()

    is_headed = request.config.getoption("--headed", default=False)

    if not is_headed:
        opts.add_argument("--headless=new")
    else:
        opts.add_argument("--start-maximized")

    for flag in (
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--window-size=1920,1080",
    ):
        opts.add_argument(flag)

    # Isolate user-data
    tmp_profile = tempfile.mkdtemp(prefix="chrome-user-data-")
    opts.add_argument(f"--user-data-dir={tmp_profile}")

    # Capture browser console logs (used by console-error assertions, e.g. GA smoke tests)
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    if browser == "chrome":
        service = ChromeService(webdriver_binary)
        drv = webdriver.Chrome(service=service, options=opts)

    elif browser == "firefox":
        service = FirefoxService(webdriver_binary)
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
    except WebDriverException:
        # Ignore errors during driver cleanup (may already be closed)
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

@pytest.fixture()
def sample_profile_image_path():
    """
    Returns an absolute path to a small image under tests/data/
    so that CreateUsecasePage.upload_logo(...) can send_keys() it.
    """
    here = os.path.dirname(__file__)    # this is a string
    profile_image_path = os.path.abspath(os.path.join(here, "tests", "data", "sample_profile_image.png"))
    if not os.path.isfile(profile_image_path):
        raise FileNotFoundError(f"Expected sample_profile_image.png at {profile_image_path}")
    return profile_image_path

@pytest.fixture()
def sample_cover_image_path():
    here = os.path.dirname(__file__)
    cover_image_path = os.path.abspath(os.path.join(here, "tests", "data", "sample_profile_image.png"))
    if not os.path.isfile(cover_image_path):
        raise FileNotFoundError(f"Expected sample_profile_image.png at {cover_image_path}")
    return cover_image_path

@pytest.fixture(scope="session")
def test_credentials():
    """
    Returns (email, password) for this worker.

    Credentials are read from consecutive TEST_EMAIL_n / TEST_PASSWORD_n pairs.
    Under pytest-xdist each worker sets PYTEST_XDIST_WORKER to gw0, gw1, … and
    gets the matching account; workers past the last configured account fall back
    to the first one. Outside xdist the slot comes from TEST_USER_INDEX (default 1).

    Provider flows create and mutate data under the account they log in as — and
    several hardcode data that only exists on account 1 — so the fallback is to
    account 1 rather than a round-robin. That does mean extra workers share one
    account, which the warning below calls out.
    """
    accounts = []
    idx = 1
    while True:
        email = os.getenv(f"TEST_EMAIL_{idx}")
        password = os.getenv(f"TEST_PASSWORD_{idx}")
        if not (email and password):
            break
        accounts.append((email, password))
        idx += 1

    assert accounts, "No credentials found — set TEST_EMAIL_1 / TEST_PASSWORD_1"

    worker = os.getenv("PYTEST_XDIST_WORKER", "")
    if worker.startswith("gw"):
        slot = int(worker[2:])
        if slot >= len(accounts):
            logging.warning(
                "%s: only %d test account(s) configured — falling back to %s, which "
                "another worker is already using. Add TEST_EMAIL_%d / TEST_PASSWORD_%d "
                "to isolate it.",
                worker, len(accounts), accounts[0][0],
                len(accounts) + 1, len(accounts) + 1,
            )
            slot = 0
    else:
        slot = int(os.getenv("TEST_USER_INDEX", "1")) - 1
        if slot >= len(accounts):
            slot = 0

    return accounts[slot]

#  ────────────────── Org write-permission gate (2026-09-09) ────────────────────

@pytest.fixture(scope="session")
def org_add_permission(test_credentials):
    """
    Names of organizations this worker's account may CREATE content in.

    The org-scoped provider flows (create dataset / prompt dataset / usecase /
    collaborative under an org) all need `canAdd` on some organization. A
    Keycloak account whose org role is `auditor` has canAdd=false and cannot pass
    those flows no matter how the UI is driven — TEST_EMAIL_2 is exactly that: a
    lone `auditor` on CivicDataLab, which is why every org-create test failed on
    gw1 while the read-only ones passed.

    That is an account-provisioning gap, not a product defect and not a test bug,
    so the flows skip with a precise reason instead of failing. Grant the account
    an `admin` (or otherwise canAdd) role on an org and they run again with no
    code change.
    """
    api = os.getenv("API_BASE_URL")
    kc, realm = os.getenv("KEYCLOAK_URL"), os.getenv("KEYCLOAK_REALM")
    cid, secret = os.getenv("KEYCLOAK_CLIENT_ID"), os.getenv("KEYCLOAK_CLIENT_SECRET")
    if not all([api, kc, realm, cid]):
        pytest.skip("API_BASE_URL / KEYCLOAK_* not configured — cannot resolve org permissions")

    import requests

    email, password = test_credentials
    payload = {
        "grant_type": "password", "client_id": cid,
        "username": email, "password": password,
    }
    if secret:
        payload["client_secret"] = secret

    try:
        tok = requests.post(
            f"{kc.rstrip('/')}/realms/{realm}/protocol/openid-connect/token",
            data=payload, timeout=30,
        )
        tok.raise_for_status()
        access = tok.json()["access_token"]
        resp = requests.post(
            f"{api.rstrip('/')}/api/graphql",
            json={"query": "query{userPermissions{organizations{organizationName roleName canAdd}}}"},
            headers={"Authorization": f"Bearer {access}"}, timeout=30,
        )
        resp.raise_for_status()
        orgs = (resp.json().get("data") or {}).get("userPermissions", {}).get("organizations") or []
    except Exception as exc:
        pytest.skip(f"Could not resolve org permissions for {email}: {exc}")

    writable = [o["organizationName"] for o in orgs if o.get("canAdd")]
    if not writable:
        roles = ", ".join(f"{o['organizationName']}={o.get('roleName')}" for o in orgs) or "no orgs"
        pytest.skip(
            f"{email} has canAdd on no organization ({roles}); org-create flows "
            f"cannot run. Grant an admin role on an org to enable them."
        )
    return writable


#  ─────────────────────── Login Fixtures (Phase 12) ─────────────────────────────

@pytest.fixture
def logged_in_provider(driver, base_url, test_credentials):
    """
    Auto-login as provider and return ProviderHomePage.
    Eliminates duplicated login setup across tests.

    Usage:
        def test_something(logged_in_provider):
            prov_home = logged_in_provider
            # ... continue test from logged-in state
    """
    from pages.home_page import HomePage

    driver.delete_all_cookies()
    email, password = test_credentials
    home = HomePage(driver, base_url)
    home.load()
    assert home.is_loaded(), "Homepage did not load successfully"

    prov_home = home.go_to_login(flow="provider", email=email, password=password)
    return prov_home

@pytest.fixture
def provider_dashboard(logged_in_provider):
    """
    Navigate to provider dashboard (My Dashboard page).
    Builds on logged_in_provider fixture.

    Usage:
        def test_something(provider_dashboard):
            my_dash = provider_dashboard
            # ... test starts from My Dashboard page
    """
    return logged_in_provider.goto_my_dashboard()


# 1) pytest_runtest_makereport
#    After each test “call” phase, if it failed and a WebDriver fixture is present,
#    take a screenshot and attach its path to item.user_properties.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Called after each test run phase. If the test “call” phase failed and the test
    has a WebDriver fixture, take a screenshot and record its relative path on
    item.user_properties, which pytest-json-report writes into report.json.
    """
    outcome = yield
    rep = outcome.get_result()

    # We only care about failures in the “call” phase
    if rep.when != "call" or not rep.failed:
        return

    # 1) See if any fixture in this test is a WebDriver instance
    driver_obj = next(
        (val for val in item.funcargs.values() if isinstance(val, WebDriver)), None
    )
    if not driver_obj:
        # No WebDriver fixture → nothing to screenshot
        return

    # 2) Make sure ./screenshots exists
    screenshots_dir = Path(os.getcwd()) / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # 3) Build a filename from the full nodeid so parametrised cases keep their own
    #    file, plus the xdist worker id so two workers never race on one path.
    worker = os.getenv("PYTEST_XDIST_WORKER", "")
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", rep.nodeid).strip("_")
    suffix = f"__{worker}" if worker else ""
    png_path = screenshots_dir / f"{stem}{suffix}.png"

    try:
        driver_obj.save_screenshot(str(png_path))
        rel = os.path.relpath(str(png_path), os.getcwd())

        # user_properties travels with the report through xdist's serialization,
        # so the controller's report.json gets the path even in parallel runs.
        item.user_properties.append(("screenshot", rel))

        print(f"\n📸 [HOOK] Saved screenshot for {rep.nodeid}: {rel}\n")
    except Exception as e:
        print(f"\n⚠️ [HOOK] Could not save screenshot for {rep.nodeid}: {e}\n")


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 2) pytest_sessionfinish
#    After pytest finishes running all tests (and after report.json is written),
#    automatically call report_generator.py to produce TEST_REPORT.md and TEST_REPORT.pdf.
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """
    Called once pytest is completely done. If report.json exists, invoke report_generator.py.
    """
    # Under xdist every worker also fires this hook; only the controller has the
    # finished report.json, so workers would race each other writing the PDF.
    if hasattr(session.config, "workerinput"):
        return

    # Nothing ran — report.json is stale from a previous session.
    if session.config.getoption("collectonly", default=False):
        return

    rpt = Path(os.getcwd()) / "report.json"
    if rpt.exists():
        print("\n\n📄 Generating TEST_REPORT.md + TEST_REPORT.pdf …")
        subprocess.run([sys.executable, "report_generator.py"], check=False)
    else:
        print("\n\n⚠️  report.json not found; skipping report generation.")

    # Accessibility runs leave structured findings behind; turn them into
    # ACCESSIBILITY_REPORT.md/.html. Skipped when the run had no a11y tests so
    # an unrelated run never overwrites the last accessibility report.
    if any((Path(os.getcwd()) / "reports" / "a11y").glob("*.json")):
        print("\n📄 Generating ACCESSIBILITY_REPORT.md + .html …")
        subprocess.run([sys.executable, "a11y_report_generator.py"], check=False)
