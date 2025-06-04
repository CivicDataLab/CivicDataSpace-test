# CivicDataSpace Automated Test Suite

A Python + Selenium test framework for the CivicDataSpace platform, covering both **consumer** and **provider** workflows. Tests are organized into smoke, functional, and mobile suites; they produce JSON/Markdown/PDF reports (with embedded screenshots) and measure coverage. A GitHub Actions workflow runs everything on each push/PR.

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Prerequisites](#prerequisites)  
3. [Installation & Setup](#installation--setup)  
4. [Environment Variables](#environment-variables)  
5. [Directory Structure](#directory-structure)  
6. [Running Tests Locally](#running-tests-locally)  
   - [Consumer Tests](#consumer-tests)  
   - [Provider Tests](#provider-tests)  
   - [Mobile Tests](#mobile-tests)  
7. [Generating Reports Locally](#generating-reports-locally)  
   - [JSON Reports](#json-reports)  
   - [Markdown & PDF Reports](#markdown--pdf-reports)  
   - [Coverage Reports](#coverage-reports)  
8. [GitHub Actions CI](#github-actions-ci)  
9. [Screenshots & Artifacts](#screenshots--artifacts)  
10. [Contributing](#contributing)  
11. [License](#license)  

---

## Project Overview

This repository implements a **Page Object Model (POM)**–based Selenium/pytest framework:

- **POM Structure**: Dedicated page classes under `pages/` and separate locator files under `locators/`.  
- **Test Suites**:  
  - `tests/consumer`  
    - `smoke/`, `functional/`, `mobile/`  
  - `tests/provider`  
    - `smoke/`, `functional/`, `mobile/`  
- **Logging & Waiting**: Uses explicit waits (`WebDriverWait`) and Python’s `logging` for detailed traceability.  
- **Reporting**:  
  - `pytest-json-report` plugin writes per-suite JSON files (`report-<flow>-<type>.json`).  
  - Custom `report_generator.py` combines JSON data into a single `report.json`, produces a human‐readable `TEST_REPORT.md` and a styled `TEST_REPORT.pdf` (with embedded failure screenshots).  
- **Coverage**: Runs `coverage run -m pytest` → `coverage report` → `coverage html`. A `.coveragerc` excludes CI/config scripts.  
- **CI Pipeline**: A single GitHub Actions YAML runs the entire matrix (consumer/provider × smoke/functional/mobile), merges JSON outputs, reruns under coverage, and publishes HTML, MD, and PDF artifacts.

---

## Prerequisites

- **macOS | Linux | Windows** with Python 3.9+.  
- [Git](https://git-scm.com/) for version control.  
- Optionally, [GitHub CLI (`gh`)](https://cli.github.com/) for repo creation.  
- **Google Chrome** (or Chromium) installed.  
- ChromeDriver binary (auto-managed by `webdriver-manager`, or install manually).  
- **Python packages** (see below).

---

## Installation & Setup

1. **Clone the repository**  
   ```bash
   git clone https://github.com/<your-username>/CivicDataSpace-test.git
   cd CivicDataSpace-test
   ```

2. **Create a virtual environment (recommended)**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   # .venv\Scripts\activate    # Windows PowerShell
   ```

3. **Install dependencies**  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   Required packages include:
   - `pytest>=7.0.0`  
   - `pytest-json-report>=1.5.0`  
   - `selenium>=4.1.0`  
   - `webdriver-manager>=3.8.0`  
   - `coverage>=6.0`  
   - `reportlab>=3.6.0`  
   - `requests>=2.28.0`

4. **Create a `.env` file in the project root**  
   Copy the sample below (replace placeholder values as needed):
   ```
   HOME_URL_DEV=''
   URL='https://civicdataspace.in/'
   LOCAL='True'

   # Provider test credentials
   PROV_TEST_EMAIL=your_provider_email@example.com
   PROV_TEST_PASSWORD=YourP@ssword

   # Consumer test credentials (if needed)
   CON_TEST_EMAIL=your_consumer_email@example.com
   CON_TEST_PASSWORD=YourC0nsumerP@ss

   # Other secrets (if any)
   API_KEY=abcdef1234567890
   ```
   The framework uses `python-dotenv` (if installed) or `os.getenv()` to pick up base URLs and credentials.

---

## Environment Variables

- `URL` : Base URL of the site (e.g., `https://civicdataspace.in/`), used by all page classes.  
- `PROV_TEST_EMAIL` & `PROV_TEST_PASSWORD`: Provider-account credentials for “provider” flows.  
- `CON_TEST_EMAIL` & `CON_TEST_PASSWORD`: Consumer-account credentials (if/when consumer login is required).  
- `LOCAL` : Set to `'True'` if running locally vs CI. (Optional flag to change browser options.)  

Make sure to add `.env` to `.gitignore` so your secrets are never committed.

---

## Directory Structure

```
CivicDataSpace-test/
├── .github/
│   └── workflows/
│       └── test_and_report.yml       # GitHub Actions CI workflow
├── assets/
│   └── logo.png                      # (Optional) Company logo for PDF reports
├── locators/
│   ├── consumer/
│   │   ├── dataset_locators.py
│   │   ├── sectors_locators.py
│   │   ├── usecase_locators.py
│   │   ├── publishers_locators.py
│   │   ├── publisher_detail_locators.py
│   │   └── about_locators.py
│   └── provider/
│       ├── provider_homepage_locators.py
│       ├── login_locators.py
│       ├── my_dashboard_locators.py
│       ├── create_dataset_locators.py
│       ├── create_usecase_locators.py
│       └── ... (others as needed)
├── pages/
│   ├── base_page.py                  # Shared BasePage with common helpers
│   ├── home_page.py                  # POM for homepage (consumer/provider entry)
│   ├── consumer/
│   │   ├── dataset_page.py
│   │   ├── sectors_page.py
│   │   ├── usecase_page.py
│   │   ├── publishers_page.py
│   │   ├── publisher_detail_page.py
│   │   └── about_page.py
│   └── provider/
│       ├── login_page.py
│       ├── provider_home_page.py
│       ├── my_dashboard_page.py
│       ├── create_dataset_page.py
│       ├── create_usecase_page.py
│       └── ... (others as needed)
├── screenshots/                      # Auto-created: failure screenshots are captured here
│   └── ... (*.png)
├── tests/
│   ├── consumer/
│   │   ├── smoke/
│   │   │   └── test_con_flow.py
│   │   ├── functional/
│   │   │   └── test_consumer_functional_*.py
│   │   └── mobile/
│   │       └── test_consumer_mobile_*.py
│   └── provider/
│       ├── smoke/
│       │   └── test_prv_001_login.py
│       ├── functional/
│       │   ├── test_prv_002_ind_create_dataset.py
│       │   ├── test_prv_003_ind_create_usecase.py
│       │   └── ...
│       └── mobile/
│           └── test_prv_mobile_*.py
├── conftest.py                       # Pytest fixtures, hooks, screenshot capture, report hooks
├── pytest.ini                        # Pytest configuration (markers, addopts, etc.)
├── .coveragerc                       # Coverage.py configuration
├── report_generator.py               # Reads report.json → builds TEST_REPORT.md + TEST_REPORT.pdf
├── requirements.txt                  # All Python dependencies
├── .env                              # (Ignored) Stores URL and credentials
└── README.md                         # ← You are here
```

---

## Running Tests Locally

All test suites rely on **ChromeDriver**, managed automatically by `webdriver-manager` or via `CHROMEDRIVER_PATH` environment variable. By default, tests run in **headed** mode unless you explicitly set headless.

### 1. Consumer Tests

Run only the consumer smoke tests:
```bash
pytest tests/consumer/smoke --json-report --json-report-file=report-consumer-smoke.json -q
```

Run consumer functional tests:
```bash
pytest tests/consumer/functional --json-report --json-report-file=report-consumer-functional.json -q
```

Run consumer mobile tests:
```bash
pytest tests/consumer/mobile --json-report --json-report-file=report-consumer-mobile.json -q
```

### 2. Provider Tests

Run provider smoke (login) tests:
```bash
pytest tests/provider/smoke --json-report --json-report-file=report-provider-smoke.json -q
```

Run provider functional tests:
```bash
pytest tests/provider/functional --json-report --json-report-file=report-provider-functional.json -q
```

Run provider mobile tests (if implemented):
```bash
pytest tests/provider/mobile --json-report --json-report-file=report-provider-mobile.json -q
```

### 3. Run All Tests in One Go

If you want to run **every** test in one invocation (no JSON report), simply:
```bash
pytest -q
```
This will execute both `consumer/` and `provider/` suites in smoke/functional/mobile subfolders.

---

## Generating Reports Locally

### JSON Reports

Each `pytest ... --json-report --json-report-file=report-<flow>-<type>.json` produces a JSON file in the working directory. Example:
```
report-consumer-smoke.json
report-provider-functional.json
report-provider-mobile.json
```

You can merge them manually or let `report_generator.py` do it.

### Markdown & PDF Reports

After you have one (or more) `report-*.json`, merge them into a single `report.json`:

```bash
python << 'EOF'
import json, glob, os
merged = {"root": os.getcwd(), "tests": []}

for fname in glob.glob("report-*.json"):
    data = json.load(open(fname, "r", encoding="utf-8"))
    merged["tests"].extend(data.get("tests", []))

# Basic summary
total  = len(merged["tests"])
passed = sum(1 for t in merged["tests"] if t.get("outcome")=="passed")
failed = sum(1 for t in merged["tests"] if t.get("outcome")=="failed")
merged["summary"] = {"
... (truncated for brevity) ...
