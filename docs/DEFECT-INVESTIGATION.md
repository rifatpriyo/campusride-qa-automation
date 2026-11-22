# CampusRide QA Lab defect investigation

The Phase 3 exercise uses fictional accounts and separate SQLite databases. `DEMO_BUG_MODE` defaults to `false`. The exercise activates for loopback requests with a local URL when the setting is `true`. The fare-edit route is registered only in defect mode. The other three defects affect the acceptance or detail path described in their reports.

## Start a local investigation

Use PowerShell in the repository root with the [Phase 1 environment](../README.md#run-on-windows) installed. Start each independent reproduction from an unused database file. The [execution guide](../manual-testing/Execution-Guide.md#demo-accounts-and-rides) lists the fictional credentials and seeded rides.

```powershell
$campusLabStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$env:CAMPUSRIDE_DB_PATH = "instance/bug-lab-$campusLabStamp.db"
$env:CAMPUSRIDE_SECURE_COOKIE = 'false'
$env:DEMO_BUG_MODE = 'true'
.\.venv\Scripts\python.exe -m app.demo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Open [local Swagger UI](http://127.0.0.1:8000/docs) and select **Try it out** on the endpoint in the case. Use the same hostname for sign-in and requests. Use separate browser profiles when a case requires two actors. Stop the server with Ctrl+C, choose a fresh database path, and set `DEMO_BUG_MODE=false` before starting a comparison run. Switching mode changes future behavior. A fresh seed restores any fixture state changed during an earlier run.

## Findings

Each finding is a **Controlled defect in local demo application**.

| Finding | How it was detected | Why it matters |
| --- | --- | --- |
| [BUG-001](../bug-reports/BUG-001.md) Unverified acceptance | Attempted assignment as Mira and checked the persisted ride in Anika's session. The response was HTTP 200 and the assignment existed on readback. | The application can assign a passenger to a rider whose approval was never recorded. |
| [BUG-002](../bug-reports/BUG-002.md) Changed fare | Booked the BDT 80 quote, submitted BDT 5 through the lab fare route, and read the ride again. | A confirmed price cannot be trusted if a later action can overwrite it. |
| [BUG-003](../bug-reports/BUG-003.md) Early rating disclosure | Completed a ride, submitted Sami's rating, and fetched details as Tariq before Tariq rated. The received score was 5. | The first score can influence the second participant's rating. |
| [BUG-004](../bug-reports/BUG-004.md) Extra contact field | Fetched authorized trip details as Tariq and inspected the JSON field set. The response included the synthetic passenger phone field. | An authorized read can still disclose fields outside the privacy contract. |

The reports give the starting fixture, exact steps, observed result, confirmed root cause, and proposed correction for each finding.

## Run the regression checks

Run the regular suite with correct behavior.

```powershell
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m pytest -q
```

Use the explicit pytest option to exercise the four defects.

```powershell
$env:DEMO_BUG_MODE = 'true'
.\.venv\Scripts\python.exe -m pytest -vv --tb=short --bug-lab tests/test_defect_regressions.py
```

Pytest exits with code `1` when the four assertions detect the deliberate defects. Each assertion checks the same requirement in both modes. The normal suite uses clean fixtures. It reads the lab setting for these four tests only when `--bug-lab` is supplied.

Run the same four checks again to verify the corrected behavior.

```powershell
$env:DEMO_BUG_MODE = 'false'
.\.venv\Scripts\python.exe -m pytest -vv --tb=short --bug-lab tests/test_defect_regressions.py
```

The checks verify the authorization response and stored assignment, the refused fare edit and stored original price, the rating values before and after both submissions, and the absence of a contact field on an otherwise successful authorized read. Each test works on a fresh database copy.

## Recorded execution

| Run | Observed result | Evidence |
| --- | --- | --- |
| Phase 1 baseline before changes | 16 passed | [Baseline](../reports/bug-lab/01-baseline.txt) |
| Full suite with defect mode off | 20 passed | [Default suite](../reports/bug-lab/02-default-suite.txt) |
| Explicit defect-mode run | 4 failed on the targeted assertions | [Defect-mode failures](../reports/bug-lab/03-defect-mode.txt) |
| Same four checks with defect mode off | 4 passed | [Corrected-mode verification](../reports/bug-lab/04-corrected-mode.txt) |
| Regular suite with the environment flag on and no pytest opt-in | 20 passed | [CI isolation](../reports/bug-lab/05-ci-isolation.txt) |
| In-process scope checks with the flag on | Two synthetic address scenarios retained the normal acceptance and detail behavior and denied the lab fare route | [Local scope](../reports/bug-lab/06-local-scope.txt) |

During Phase 3 the browser tool reported `The browser access host is unavailable`. The terminal logs above record the observations from that exercise. Phase 6 added a [screenshot of the archived failure output](../reports/screenshots/archived-defect-run.png).

## What to communicate to developers

- Name the requirement that failed and identify the first observable difference. Provide the response code, the returned field or state, and the follow-up read when persistence matters.
- Include the exact starting ride state, user role, endpoint, and inputs. Distinguish the action that triggers the defect from the request that observes it.
- Separate observed behavior from cause. Cite the code path once confirmed and explain the user impact that drives severity and priority.
- Give a retest condition with both the restricted and legitimate behavior. An unverified rider must be denied while an approved rider can still accept. Ratings must stay private after the first submission and appear after both. Ride detail must still load for authorized participants with its approved fields.
