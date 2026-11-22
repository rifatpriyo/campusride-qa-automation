# Run the CampusRide API tests

## Start a fresh local database

From the repository root in PowerShell, use the Python environment from the [project setup](../README.md#run-on-windows). Run these commands together so seeding and Uvicorn use the same file and settings.

```powershell
$apiStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$env:CAMPUSRIDE_DB_PATH = "instance/api-testing-$apiStamp.db"
$env:CAMPUSRIDE_SECURE_COOKIE = 'false'
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m app.demo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Use [health](http://127.0.0.1:8000/health) to confirm that this server is ready. The [local Swagger UI](http://127.0.0.1:8000/docs) shows the routes and schemas.

To reset after a run, stop the test server with Ctrl+C and repeat the block with a new timestamp. The collection creates a fixed fictional student and changes ride and verification state. A fresh file restores the starting fixtures and keeps development data separate.

## Import and run in Postman

1. Import [the collection](CampusRide.postman_collection.json) and [the environment](CampusRide.local.postman_environment.json).
2. Select **CampusRide QA Lab Local** as the active environment. Keep `base_url` set to the loopback server you just started. If you changed the port, update the local environment value to match, with no trailing slash.
3. In the Collection Runner, select the entire **CampusRide QA Lab API tests** collection. Run one iteration in order, beginning with the health and authentication folder.
4. Verify that all 61 requests ran. The collection uses the cookies returned by the login requests and the quote and ride IDs returned by creation requests.

The exported environment contains a fictional shared password and fictional campus email addresses. The collection disables the automatic cookie jar for these requests and sends each role's run-scoped cookie explicitly. Keep the collection together when running it so later requests have access to those temporary values.

### Run with Newman

In a second PowerShell session with Node.js installed, run the collection against the same fresh server.

```powershell
$campusCollection = 'api-testing/CampusRide.postman_collection.json'
$campusApiEnvironment = 'api-testing/CampusRide.local.postman_environment.json'
npx.cmd --yes newman@6.2.1 run $campusCollection -e $campusApiEnvironment --ignore-redirects --timeout-request 10000
```

Add `--env-var "base_url=http://127.0.0.1:PORT"` when the local server uses a different port. Newman reports request execution and assertions separately. A successful `403` assertion means the denial matched the contract. A run stopped during setup is incomplete even if its failure count is zero.

## Run Pytest

Use the pinned Python test dependencies and run the complete suite from the repository root.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m pytest -q -ra
```

Pytest uses FastAPI TestClient with a temporary SQLite copy per test. The [Phase 3 lab option](../docs/DEFECT-INVESTIGATION.md#run-the-regression-checks) belongs to an explicit defect exercise. The regular command runs the same business-rule checks in normal mode.

## Recorded verification

Both suites ran on Windows on 22 Nov 2026 with `DEMO_BUG_MODE=false`. Newman 6.2.1 used a fresh seeded server at `http://127.0.0.1:8768`. Pytest 9.2.0 used in-process clients and temporary SQLite copies.

| Runner | Executed | Passed | Failed | Skipped |
| --- | --- | --- | --- | --- |
| Pytest | 32 tests | 32 | 0 | 0 |
| Newman | 61 requests and 240 assertions | 240 assertions | 0 | 0 |

A separate invalid-configuration check confirmed that an invalid `base_url` fails before any requests are sent. Share assertion totals or redacted evidence. Raw Newman JSON reports can contain temporary session cookies.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Connection refused or the health request fails | Start Uvicorn and confirm the selected loopback URL and port match the server. |
| The collection skips requests before reaching the server | Choose the local Postman environment and set `base_url` to a loopback HTTP URL with an explicit port. |
| The normal-mode contract check fails | Restart the server with `DEMO_BUG_MODE=false` in the server's PowerShell session. |
| A later step returns `401` | Check the relevant sign-in result and run every folder in order. Confirm the demo accounts were seeded. |
| Registration returns `409` on the first registration step | Stop the test server and start it on a fresh seeded database. |
| A quote fails with `409` | Confirm that the quote was created in the current run and redeemed before it expired. |
| A rule returns an unexpected status or payload | Inspect the preceding assertion and the exact [case](API-Test-Cases.md). Compare the request, actor, and starting state before changing a test. |

See the [test plan](API-Test-Plan.md) for the status code contract and expected coverage.
