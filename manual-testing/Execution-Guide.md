# CampusRide QA Lab manual execution guide

## Start an isolated demo

Use PowerShell from the repository root. If the Phase 1 environment is already installed, start at the environment variable commands.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:CAMPUSRIDE_DB_PATH = 'instance/campusride-manual.db'
$env:CAMPUSRIDE_SECURE_COOKIE = 'false'
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m app.demo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use the [app](http://127.0.0.1:8000/), [Swagger UI](http://127.0.0.1:8000/docs), and [health endpoint](http://127.0.0.1:8000/health). A healthy app returns HTTP `200` and `{"status":"ok"}`. Keep the same base URL in each browser or shell. Environment variables are per PowerShell session. Set them again if you open a new session for seeding or starting the server.

## Demo accounts and rides

All seeded accounts use the fictional password `CampusDemo2026!`.

| Use | Email | Initial access | Women-only flag |
| --- | --- | --- | --- |
| Mira Rahman | `mira@campus.example` | Passenger, unverified as rider | On |
| Anika Karim | `anika@campus.example` | Passenger and approved rider | On |
| Tariq Hasan | `tariq@campus.example` | Passenger and approved rider | Off |
| Sami Chowdhury | `sami@campus.example` | Passenger, pending rider request | Off |
| Nadia Ahmed | `admin@campus.example` | Admin | Off |

Sami's fresh request has reference `MOCK-SAMI26`. The fresh seed assigns Sami account ID 4. Use `GET /api/auth/me` to confirm IDs on a database that already has student records.

| Seed ID | Initial status | Passenger / rider | Route and fare | Preference |
| --- | --- | --- | --- | --- |
| #1 | Completed | Mira / Anika | Engineering Hall to North Gate, BDT 60 | Women-only |
| #2 | Cancelled | Sami / unassigned | Main Library to North Gate, BDT 50 | Regular |
| #3 | In progress | Sami / Tariq | Engineering Hall to Residence Quad, BDT 60 | Regular |
| #4 | Accepted | Mira / Tariq | Student Center to Engineering Hall, BDT 50 | Regular |
| #5 | Requested | Anika / unassigned | Residence Quad to Student Center, BDT 50 | Regular |
| #6 | Requested | Mira / unassigned | Main Library to Residence Quad, BDT 70 | Women-only |
| #7 | Requested | Mira / unassigned | North Gate to Engineering Hall, BDT 60 | Regular |

Both ratings already exist for #1. Ride #3 has both start confirmations and neither completion confirmation, so completing it creates a trip with empty ratings. For new rides, record the returned ID rather than assuming the next number.

The quote endpoints use these stop values in fare zone order.

| Zone | Stop | API value |
| --- | --- | --- |
| 0 | North Gate | `north_gate` |
| 1 | Main Library | `main_library` |
| 2 | Engineering Hall | `engineering_hall` |
| 3 | Student Center | `student_center` |
| 4 | Residence Quad | `residence_quad` |

## Reset to a fresh seed

Stop the test server with Ctrl+C. Point the next run at a new file to preserve earlier test evidence and leave the default demo database intact.

```powershell
$qaStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$env:CAMPUSRIDE_DB_PATH = "instance/campusride-manual-$qaStamp.db"
$env:CAMPUSRIDE_SECURE_COOKIE = 'false'
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m app.demo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Sign in again in each profile. Sessions belong to the previous database. When seed IDs matter, compare the new admin totals with the fixture table before changing records. Running the seed again on the same file reports that demo data already exists and preserves its state.

## Run a case manually

1. Open [Test-Cases.xlsx](Test-Cases.xlsx) and select a row. Read its prerequisites and note the requirement ID before acting.
2. For UI steps, sign in with the required account. Use a distinct browser profile for each role. A second tab or another private window in the same profile can share the same cookie. Refresh the other participant's page after each action unless testing stale state.
3. For HTTP steps, sign in through the web app or execute `POST /api/auth/login` in Swagger UI. Enter the seeded email and password as JSON. Open the specified endpoint, select **Try it out**, supply the path parameters or body, then select **Execute**. Check the response code and body. `GET /api/auth/me` verifies which role owns that session.
4. Use the API field names and values in the case row. For quote-based booking, call `POST /api/rides/quote`, capture its `id` and `expires_at`, then send just `{"quote_id":"<id>"}` to `POST /api/rides` unless the case tests invalid fields. The [README](../README.md#try-the-api) has a sample quote request.
5. For the race case, arrange two separately signed-in windows or two testers. Prepare both acceptance requests before anyone submits. Attempt them on the same cue and capture both response codes. Compare request start times and durations from the browser Network panel or sanitized HAR exports. The requests overlap when the later start precedes the earlier finish. With only a stale second attempt, record that observation and rerun the race on a fresh ride.

### Individual requests from PowerShell

For a direct check, use `curl.exe` with one test-only cookie file per account. The following commands sign in as Mira and inspect the active role. Change the base URL if the test server uses another port.

```powershell
$qaBase = 'http://127.0.0.1:8000'
$qaCookie = Join-Path $env:TEMP 'campusride-qa-mira.cookies'
'{"email":"mira@campus.example","password":"CampusDemo2026!"}' |
  curl.exe -sS -w '\nHTTP %{http_code}\n' -c $qaCookie -H 'Content-Type: application/json' --data-binary '@-' "$qaBase/api/auth/login"
curl.exe -sS -w '\nHTTP %{http_code}\n' -b $qaCookie "$qaBase/api/auth/me"
```

Add `-X POST` for actions that take no body, such as `/api/rides/7/accept`. For a JSON body, pipe the input as on the login line. For TC-006, keep the original test cookie file when you send the sign-out request with `-b` only, then deliberately retry `/api/auth/me` with that file to verify revocation. Use `-i` to inspect headers locally and redact the cookie value from recorded evidence. Remove temporary cookie files after the test.

### Read-only database check for TC-007

Start `.\.venv\Scripts\python.exe` in the same PowerShell session after signing Mira in. The following uses the explicit test database path and outputs comparison results only. Paste the session token from the browser's cookie panel or a local test cookie file when prompted.

```python
import getpass, hashlib, os, sqlite3
from datetime import UTC, datetime
from pathlib import Path
path = Path(os.environ["CAMPUSRIDE_DB_PATH"]).resolve()
db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
sql = "SELECT password_hash FROM users WHERE email IN (?, ?) ORDER BY email"
rows = db.execute(sql, ("anika@campus.example", "mira@campus.example")).fetchall()
a_salt, a_hash = rows[0][0].split(":")
m_salt, m_hash = rows[1][0].split(":")
key = lambda salt: hashlib.scrypt(b"CampusDemo2026!", salt=bytes.fromhex(salt), n=2**15, r=8, p=3, dklen=32, maxmem=64 * 1024**2).hex()
print("Distinct salts", a_salt != m_salt)
print("Both scrypt digests match", key(a_salt) == a_hash and key(m_salt) == m_hash)
token = getpass.getpass("Temporary Mira session token: ")
digest = hashlib.sha256(token.encode()).hexdigest()
row = db.execute("SELECT expires_at FROM login_sessions JOIN users ON users.id = login_sessions.user_id WHERE email = ? AND token_hash = ?", ("mira@campus.example", digest)).fetchone()
print("Stored digest with future expiry", bool(row and datetime.fromisoformat(row[0]).replace(tzinfo=UTC) > datetime.now(UTC)))
db.close()
```

## Record results and file defects

- Enter what you observed in **Actual Result**, including the response code, returned value, or visible state. Keep the date and time zone, app build, browser or HTTP client, and affected IDs in **Notes** or the linked evidence.
- Select **Pass**, **Fail**, **Blocked**, or **Not Run** in the status dropdown. A validation or authorization case passes when the observed rejection and any specified state checks match. Record a blocker if a missing prerequisite stops an attempted case. Leave unexecuted cases as Not Run.
- Save evidence with a name such as `TC-019_20261122_tariq-response.txt`. Redact tokens and hashes and avoid including credentials in screenshots. In the workbook, enter the evidence reference under **Notes**.
- For a failure, copy the [bug report template](Bug-Report-Template.md). Use a title that identifies the action and observed behavior. Record the fixture, account role, exact inputs and steps, and the expected versus actual results. For timing-dependent issues, include the number of attempts, both responses, and the final state.
- Assign severity by impact and priority by urgency. Add the bug ID to the test row. Record the fix build and retest result in the report after repeating the same case on a clean fixture.
