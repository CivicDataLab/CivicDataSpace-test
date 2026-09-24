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
        # Headless pins a viewport; headed maximises to the real screen. Those
        # are different widths and can land on different responsive breakpoints,
        # so a layout bug can be headless-only. Overridable to test exactly that.
        f"--window-size={os.getenv('WINDOW_SIZE', '1920,1080')}",
    ):
        opts.add_argument(flag)

    # Isolate user-data
    tmp_profile = tempfile.mkdtemp(prefix="chrome-user-data-")
    opts.add_argument(f"--user-data-dir={tmp_profile}")

    # Kill Chrome's own password bubbles. The leak-detection dialog ("The
    # password that you just used was found in a data breach") is BROWSER UI,
    # not page content: it renders over the page and swallows clicks, while
    # being invisible to page_source, the console log and the network log.
    # That combination is what made test_prv_006 look impossible -- a modal
    # whose button was unique, visible, enabled and correctly selected, with a
    # clean console and no mutation ever sent. It also fires per PASSWORD, so
    # it hit the accounts whose credentials are in a breach corpus and not
    # others, which read as an account/org-specific failure that it never was.
    opts.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )
    opts.add_argument("--disable-features=PasswordLeakDetection,AutofillServerCommunication")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-notifications")

    # Capture browser console logs (used by console-error assertions, e.g. GA smoke tests)
    # "performance" carries Chrome's Network.* events, which is the only way to
    # assert on what the app actually requested. Tests that count requests need
    # it; adding it here rather than in a second driver fixture keeps
    # chromedriver resolution (below) in one place - duplicating that setup is
    # what broke consumer-smoke with a driver/browser version mismatch.
    opts.set_capability(
        "goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"}
    )

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

def _account_index() -> int:
    """Which TEST_EMAIL_<n> slot this worker uses. gw0→1, gw1→2, gw2→3 …

    A plain helper, not a fixture -- `writable_org` and `test_credentials` both
    need it, and session-scoped fixtures cannot be called directly.
    """
    worker = os.getenv("PYTEST_XDIST_WORKER", "")
    if worker.startswith("gw"):
        return int(worker[2:]) + 1
    return int(os.getenv("TEST_USER_INDEX", "1"))


@pytest.fixture(scope="session")
def test_credentials():
    """
    Returns (email, password) for this worker.

    Under pytest-xdist each worker sets PYTEST_XDIST_WORKER to gw0, gw1, …
    gw0 → TEST_EMAIL_1 / TEST_PASSWORD_1
    gw1 → TEST_EMAIL_2 / TEST_PASSWORD_2
    Falls back to TEST_USER_INDEX (or 1) when not running under xdist.
    """
    idx = _account_index()

    email = os.getenv(f"TEST_EMAIL_{idx}")
    password = os.getenv(f"TEST_PASSWORD_{idx}")

    # fall back to user 1 if the derived slot has no credentials configured
    if not (email and password):
        email = os.getenv("TEST_EMAIL_1")
        password = os.getenv("TEST_PASSWORD_1")

    assert email and password, f"No credentials found for worker slot {idx}"
    return email, password

#  ────────────────── Org write-permission gate (2026-09-09) ────────────────────

@pytest.fixture(scope="session")
def org_add_permission(test_credentials):
    """
    Names of organizations this worker's account may CREATE content in.

    The org-scoped provider flows (create dataset / prompt dataset / usecase /
    collaborative under an org) all need `canAdd` on some organization. A
    Keycloak account whose org role is `auditor` has canAdd=false and cannot pass
    those flows no matter how the UI is driven.

    That is an account-provisioning gap, not a product defect and not a test bug,
    so the flows skip with a precise reason instead of failing. Grant the account
    an `admin` (or otherwise canAdd) role on an org and they run again with no
    code change.

    Current roles (verified live against dev 2026-09-18 via this exact query —
    re-check here before trusting this comment, don't just read it; it has
    already gone stale twice: once when TEST_EMAIL_2's role changed, and again
    when TEST_EMAIL_3 was moved off "my test agency" onto its own org):

    - TEST_EMAIL_1 — admin/canAdd=true on 11 orgs (CivicDataLab, Open Budgets
      India, JusticeHub, "my test agency", "test org name", ASDMA, HPSDMA, The
      Rockefeller Foundation, Patrick J. McGovern Foundation, BMA, Gates
      Foundation). Broadest account by far.
    - TEST_EMAIL_2 — admin/canAdd=true on "my test agency" only; still
      auditor/canAdd=false on CivicDataLab.
    - TEST_EMAIL_3 — admin/canAdd=true on "test org name" only. Was originally
      provisioned on "my test agency" alongside TEST_EMAIL_2 (2026-09-17),
      which meant both accounts landed on the *same* org via
      `OrganizationsPage.select_org()`'s hardcoded preference below — real,
      reproducible write contention on that one org row under concurrent
      (`-n 3`) CI runs (test_prv_006/007 failing on whichever worker held
      TEST_EMAIL_3). Moved to "test org name" 2026-09-18 specifically to
      eliminate that collision, not just to add coverage.

    Correction to a claim this docstring used to make: this fixture's
    `writable` list IS whatever the live permissions query returns, but the
    org a test actually lands on in the browser is NOT picked from it
    dynamically. `OrganizationsPage.select_org()` hardcodes a preference for
    `OrgLocators.ORG_TEST` ("my test agency") first, falling back to "the
    first available org card" only if that specific one isn't clickable for
    the logged-in account. So which org two concurrently-running accounts
    collide on is determined by that hardcoded locator, not by this fixture —
    keep that coupling in mind before granting/revoking canAdd on "my test
    agency" for any future account.
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


# One org per account, so two concurrent workers never write the same org row.
# Verified live 2026-09-24: account 1 has canAdd on all three; account 2 on
# "my test agency" + "test org 2"; account 3 on "test org name" only.
# Override per slot with TEST_ORG_1 / TEST_ORG_2 / TEST_ORG_3.
DEDICATED_ORG_BY_ACCOUNT = {
    1: "my test agency",
    2: "test org 2",
    3: "test org name",
}


@pytest.fixture(scope="session")
def writable_org(org_add_permission):
    """The single organization this worker's account may write to.

    Every org-scoped provider flow must go through this, not
    `org_add_permission[0]` and not `select_org()`'s old hardcoded preference.
    Both of those let two workers land on the SAME org concurrently:

    - `select_org()` with no argument fell back to "my test agency", which
      account 1 can write to, while account 2's `org_add_permission[0]` IS
      "my test agency" -- so test_prv_009 (which edits the org profile) and
      test_prv_006/007/011 (which create under it) ran against one org row at
      the same time. That is CivicDataSpace-test#103.
    - `org_add_permission[0]` is just whatever the permissions query returns
      first; for account 1 that is "CivicDataLab", a real org rather than a
      test one.

    Skips loudly rather than silently colliding, because the provisioning this
    depends on has already drifted twice.
    """
    idx = _account_index()
    want = os.getenv(f"TEST_ORG_{idx}") or DEDICATED_ORG_BY_ACCOUNT.get(idx)

    if want and want in org_add_permission:
        return want

    if want:
        pytest.skip(
            f"Account slot {idx} is meant to use '{want}' exclusively but has no "
            f"canAdd on it (writable: {', '.join(org_add_permission)}). Grant an "
            f"admin role on '{want}', or set TEST_ORG_{idx}."
        )

    # Unmapped slot (more workers than configured accounts): fall back, but
    # prefer an org no other slot claims so we still do not collide.
    claimed = set(DEDICATED_ORG_BY_ACCOUNT.values())
    unclaimed = [o for o in org_add_permission if o not in claimed]
    return unclaimed[0] if unclaimed else org_add_permission[0]


@pytest.fixture(scope="session")
def backend_enum_labels():
    """Labels the frontend shows for a backend GraphQL enum, sorted.

    The frontend compiles enum values in at build time and labels each as its name
    with underscores as spaces; this reads the same values live from the backend.
    """
    import requests

    api = os.getenv("API_BASE_URL")
    assert api, "API_BASE_URL is not set: cannot read backend enums"

    def labels(enum_name: str) -> list[str]:
        resp = requests.post(
            f"{api.rstrip('/')}/api/graphql",
            json={"query": '{__type(name:"%s"){enumValues{name}}}' % enum_name},
            timeout=30,
        )
        resp.raise_for_status()
        enum_type = (resp.json().get("data") or {}).get("__type")
        assert enum_type, f"Backend has no GraphQL enum {enum_name}"
        return sorted(v["name"].replace("_", " ") for v in enum_type["enumValues"])

    return labels


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