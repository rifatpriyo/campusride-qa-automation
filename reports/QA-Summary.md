# CampusRide QA summary

Reviewed on **22 November 2026**. CampusRide is an independent educational project for a fictional campus. The review follows a passenger's booking from fare preview to completion and examines which actions each participant can take along the way.

## Execution results

| Evidence | Unit | Passed | Failed | Skipped | Not run |
| --- | --- | ---: | ---: | ---: | ---: |
| [Manual execution workbook](../manual-testing/Test-Cases.xlsx), Phase 2 | 33 designed cases | 29 | 0 | — | 4 |
| [Backend and API run](execution/backend-pytest.txt), Phase 6 | 32 collected Pytest cases | 32 | 0 | 0 | 0 |
| [Headless Chromium run](execution/ui-pytest.txt), Phase 6 | 18 collected Pytest cases | 18 | 0 | 0 | 0 |
| [Newman collection run](execution/newman-summary.txt), Phase 6 | 240 assertions across 61 requests | 240 | 0 | 0 | 0 |

The manual workbook also records zero blocked cases. Its statuses use **Not Run** for an unexecuted case. The 29 passes are historical results from direct HTTP requests, rendered HTML checks and a read-only database inspection. Automated checks of related behavior leave those manual records intact. A single Postman request can run several assertions, so the rows have different counting units.

The Phase 6 UI run emitted one Pytest fixture deprecation warning from the Playwright plugin. A separate Phase 5 diagnostic verified that failure reports preserve a screenshot and trace for each actor. [Browser execution record](../automation/README.md#verified-run)

## Environment and test data

The local evidence comes from Windows, Python 3.11.5, FastAPI, Uvicorn and SQLite. Backend tests use in-process FastAPI clients with a fresh database copy per test. Browser tests use Python Playwright with Chromium 159, a loopback server, and separate browser sessions for each actor. Newman runs the collection in order against a fresh seeded server. The normal suites use `DEMO_BUG_MODE=false`. [Backend setup](../api-testing/README.md) · [Browser setup](../automation/README.md)

The repeatable seed contains five fictional accounts and seven rides in different states. It includes approved and unverified students, a pending application, and a restricted request with both an eligible and an ineligible rider available for comparison. [Demo accounts and ride states](../manual-testing/Execution-Guide.md#demo-accounts-and-rides)

## Modules and methods

| Module | Test approach | Example observation |
| --- | --- | --- |
| Accounts, sessions and admin review | Boundary values, role-based tests and negative cases | A 9-character password was rejected. A valid 10-character password was accepted. Approval gave a pending student access to the rider listing. |
| Fare preview and booking | Input validation, known fare calculations and quote lifecycle | North Gate to Residence Quad quoted BDT 80. Changing the destination invalidated the displayed quote until the passenger requested another. |
| Listing, assignment and cancellation | Eligibility comparisons, competing requests and saved-state checks | The two-client acceptance check expects one successful assignment and one conflict. A separate browser scenario checks the losing rider's stale listing. |
| Trip start, completion and ratings | State-transition tests from both participants' views | One completion confirmation left the ride in progress. Once both submitted ratings, each saw the other's score. |
| Local setup and API responses | Seed repeatability, health checks and response contract assertions | Tests check the HTTP status, required fields, types and the permitted fields in ride responses. |

## Requirement coverage and open manual cases

All **16 documented requirements** map to written manual cases. **15 of 16** have at least one mapped case with a recorded manual pass. **10 of 16** have a pass recorded for every mapped manual case. REQ-008 has a written case for exclusive acceptance and separate automated evidence from the concurrent API test. [Requirements](../docs/REQUIREMENTS.md) · [Traceability matrix](../manual-testing/Traceability-Matrix.xlsx) · [Backend ride tests](../tests/test_rides.py)

| Not Run | Manual evidence still needed |
| --- | --- |
| TC-013 | A tester previews the fare in the browser before confirming the booking. |
| TC-022 | Two eligible riders compete for one open request, with evidence of overlapping attempts and the final assignment. |
| TC-024 | Both assigned participants' pre-start cancellation variants are observed on separately restored fixtures. |
| TC-032 | A tester checks the desktop and narrow layouts, stable controls and interactive Swagger workflow. |

## Controlled defect findings

Each entry is a **Controlled defect in local demo application**. In the archived exercise, all four regression assertions failed with the defects enabled. On fresh data with normal behavior restored, the same four assertions passed. These are the outcomes of the two Phase 3 runs. [Defect-mode output](bug-lab/03-defect-mode.txt) · [Normal-mode comparison](bug-lab/04-corrected-mode.txt)

| Finding | Affected rule | Result observed in the exercise |
| --- | --- | --- |
| [BUG-001](../bug-reports/BUG-001.md) | Rider approval | An unverified student obtained an assignment. |
| [BUG-002](../bug-reports/BUG-002.md) | Fixed fare | The saved price changed after the passenger had booked. |
| [BUG-003](../bug-reports/BUG-003.md) | Independent ratings | One participant saw the other person's score before submitting their own. |
| [BUG-004](../bug-reports/BUG-004.md) | Ride-detail response fields | A detail response included a synthetic phone number outside its approved fields. |

## Final repository review

- Validated both workflow triggers, all three job configurations and their dependency paths. All six shell command blocks passed Bash syntax checking. Repeated both Pytest suites from a copy containing only repository files, using the installed test environment. The export commands produced JUnit XML for 32 backend and 18 browser cases, plus a self-contained Chromium HTML report. The Newman JUnit export contained 240 assertion cases across 61 requests. All three XML reports recorded zero failures, errors and skips.
- Checked relative Markdown links and heading anchors, parsed the Python and JSON files, checked workbook integrity, and ran `pip check` against the installed environment. The dependency check passed. The local runs used reusable seed data and separate actor sessions for multi-user cases.
- Inspected tracked and proposed files for SQLite data, private key material, recognizable service tokens and literal session cookies. That inspection found only the documented demo credentials. Git exclusions cover local databases, environment files, virtual environments, browser traces and generated runner output. Selected screenshots and execution summaries are retained as portfolio evidence.

## Limitations and recommendations

1. Finish the four open workbook cases and record the build, actor, starting state and actual observation for each. Prioritize TC-022 for its timing requirement and TC-032 for the outstanding layout review.
2. Browser automation exercised Chromium. Add a keyboard-only and small-viewport review of booking and cancellation before making an accessibility or mobile usability claim.
3. The fixtures use mock verification, fixed stops and simulated fares. The small SQLite data set supports functional checks. Production traffic, real payments, GPS and real identity verification are outside this project's scope.
4. Check the first GitHub-hosted workflow run and retain its run URL and artifacts. The local results above establish execution on Windows. The workflow defines the hosted run. [GitHub Actions workflow](../.github/workflows/qa-tests.yml)
