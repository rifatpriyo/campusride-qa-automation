# CampusRide UI automation

This suite uses Python Playwright, Pytest, and Chromium to exercise the existing CampusRide pages through the browser. Run the commands below from the repository root.

## Install the dependencies and browser

Use Python 3.11 or newer. Create the virtual environment with `py -3.11 -m venv .venv` if you need one, then install the app, its test dependencies, and Playwright's Chromium build.

```powershell
.\.venv\Scripts\python.exe -m pip install -r automation/requirements.txt
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) 'instance\playwright-browsers'
.\.venv\Scripts\python.exe -m playwright install chromium
```

The commands use an ignored browser cache inside the project. Set the same `PLAYWRIGHT_BROWSERS_PATH` in each new terminal used to run Playwright.

## Run the tests

Run all browser scenarios headless.

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) 'instance\playwright-browsers'
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m pytest -c automation/pytest.ini automation/tests -v
```

Run a single scenario. This example writes a separate report so the full run stays available.

```powershell
.\.venv\Scripts\python.exe -m pytest -c automation/pytest.ini automation/tests/test_authentication.py::test_student_signs_in_with_valid_credentials --html automation/reports/debug-report.html --output automation/reports/debug-artifacts
```

Add `--headed` to open a visible Chromium window in a desktop session. The optional `--slowmo 300` setting slows browser actions for debugging. The root `python -m pytest` command runs the backend suite.

## Test data and isolation

`conftest.py` seeds a temporary SQLite database once per test session using the app's demo seed, then copies it for each test. It starts the app on an available `127.0.0.1` port with `DEMO_BUG_MODE=false` and stops it during teardown. `sign_in` uses the fictional demo accounts and opens a fresh browser context per actor, so tests can independently reload and verify actions taken by a second participant. Rerunning a test restores its initial data automatically.

| Seeded data | Used for |
| --- | --- |
| Mira, unverified passenger | Sign-in, booking, cancellation, and access controls |
| Anika and Tariq, approved riders | Acceptance and eligibility. Anika is women-only eligible and Tariq is ineligible. |
| Sami, pending rider applicant | Admin approval and passenger-side trip actions |
| Nadia, admin | Reviewing Sami's application |
| Ride #3, Sami and Tariq | In-progress trip with both start confirmations and no completion confirmations |
| Ride #4, Mira and Tariq | Accepted trip with no start confirmations |
| Ride #6, women-only request, and ride #7, regular request | Eligibility, acceptance, and cancellation |

## Coverage

| Area | Tests | What the browser verifies |
| --- | ---: | --- |
| Authentication | 4 | Valid and invalid sign-in, required fields, and redirect to sign-in after sign-out |
| Booking | 4 | Regular booking, same-stop rejection, fare preview and requote, and display on the passenger dashboard |
| Rider and eligibility | 4 | Approved acceptance, unavailable controls for unverified riders, a rejected second acceptance from a stale page, and women-only listing visibility |
| Trip management and ratings | 4 | Cancellation and ride history, one versus two completion confirmations, start confirmations, and mutual disclosure of ratings |
| Admin | 2 | Approval grants rider access and a student opening `/admin` receives the forbidden page |

The unverified-rider scenario verifies that the dashboard offers no acceptance controls. Direct API authorization and simultaneous acceptance are covered in the [backend API suite](../api-testing/API-Test-Cases.md). Run instructions for the deliberate defects are in the [controlled defect exercise](../docs/DEFECT-INVESTIGATION.md).

## Reports and failure evidence

Open `automation/reports/ui-report.html` in a browser. Pytest HTML lists each test's result and duration, and shows assertion details for failures. The report embeds failure screenshots and links to retained traces under `automation/reports/artifacts/`. A failed test with multiple actor contexts can retain a trace for each context.

To inspect a saved trace, open the ZIP in Playwright's Trace Viewer.

```powershell
.\.venv\Scripts\python.exe -m playwright show-trace 'automation/reports/artifacts/<test-folder>/trace.zip'
```

The next run replaces its report and artifact directory. Keep the HTML and artifacts together when saving a failed run. Generated reports are ignored by Git.

## Verified run

On November 22, 2026, the Windows headless run with Python 3.11.5 and Chromium 159 produced 18 passes, zero failures, and zero skips. A separate headed sign-in check passed. An intentional diagnostic failure produced two screenshots and two trace archives, one of each per actor. The normal backend run passed all 32 tests.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Chromium executable is missing | Set `PLAYWRIGHT_BROWSERS_PATH` to the directory used for installation, then run `python -m playwright install chromium` from the virtual environment. |
| Pytest rejects browser or report options | Run the install command for `automation/requirements.txt` with the same Python interpreter used for Pytest. |
| The local app fails to start | Check the server logs captured by Pytest and confirm the environment permits binding to `127.0.0.1`. The fixture allocates its own port. |
| A partner's action looks stale | Refresh the second participant's page. Multi-user tests do this after the first participant sees the persisted change. |
| A test fails before a page opens | Read the setup traceback in the report or terminal. Playwright captures screenshots from open pages and records traces for browser contexts. |

The plugin guides describe browser options, failure artifacts, and HTML reporting. [Playwright Pytest plugin reference](https://playwright.dev/python/docs/test-runners), [pytest-html user guide](https://pytest-html.readthedocs.io/en/stable/user_guide.html).
