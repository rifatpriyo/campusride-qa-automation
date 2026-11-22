# CampusRide QA Lab manual test plan

## Project overview

CampusRide QA Lab is a local ride-sharing application for a fictional university. Phase 1 lets students register, request a ride at a quoted fare, and apply for rider approval. Approved riders can accept eligible requests. Both participants confirm start and completion separately, then rate each other. Administrators review rider applications and monitor activity.

The test basis is the [Phase 1 requirements](../docs/REQUIREMENTS.md), the implemented routes and models, and the demo data created by `app.demo`. [Test cases](Test-Cases.xlsx) hold execution results. The [traceability matrix](Traceability-Matrix.xlsx) maps the case design to the requirements.

## Testing objectives

- Verify that a student can progress from registration through a completed ride using the implemented roles.
- Check authorization at the server boundary, especially rider approval, women-only rides, admin decisions, and ride detail access.
- Check that a booking preserves the quoted BDT fare and that an open request has at most one assigned rider.
- Verify state transitions and rating privacy by observing both participants' views.
- Produce reproducible evidence for test results and defects.

## Scope

| Area | Coverage |
| --- | --- |
| Accounts and roles | Campus email and password validation, duplicate accounts, sign-in, sign-out, credential storage, passenger and rider access, and admin permissions |
| Rider verification | Mock reference validation, submission, approval, rejection, and resubmission |
| Booking and fares | Fixed stops, ride preferences, preview, deterministic fare, quote expiration, quote ownership, and one-time redemption |
| Ride management | Listing and acceptance, women-only eligibility, self-acceptance rules, competing acceptances, and cancellation boundaries |
| Trip lifecycle | Independent start and completion, invalid state transitions, rating bounds, and score disclosure |
| Local interfaces | Passenger, rider, and admin pages, narrow and wide layouts, stable browser controls, health, Swagger UI, and seed repeatability |

### Out of scope

Real payments, live location, mapping, identity document handling, messaging, email delivery, and account recovery. Load testing, a security audit, physical-device and assistive-technology testing, automated API collections, browser automation, and CI/CD are outside this phase.

## Testing approach

- Use equivalence partitions and boundary values for campus email, password length and composition, mock references, route inputs, and rating scores.
- Apply role and state transition tests from independent passenger, rider, and admin sessions. Verify both the response and the resulting ride or approval state where the case specifies it.
- Exercise the user interface with keyboard and pointer at desktop and narrow widths. Use Swagger UI or individual local HTTP requests for server-side negative cases and exact status codes.
- For competing acceptances, prepare two eligible sessions against the same requested ride. Record both responses and the final assignment, with timing evidence to distinguish overlapping requests from a stale second attempt.
- Use a read-only SQLite inspection for the storage case. Capture only the outcome of credential and token comparisons.

## Test environments

| Environment | Configuration |
| --- | --- |
| Application | Phase 1 app version 0.1.0, Python 3.11 or newer, Uvicorn on loopback, and a separate SQLite test database |
| Browser | Chrome or Edge with JavaScript enabled. Use a desktop window and an emulated viewport around 390 × 844 pixels. Record the actual browser and version on execution. |
| Multiple roles | Use distinct browser profiles or different browsers so each role keeps its own session. |
| Direct checks | Windows PowerShell with Swagger UI or individual `curl.exe` requests. Use one hostname and port for the run. |

## Test data

Use the [demo account and ride fixtures](Execution-Guide.md#demo-accounts-and-rides). The fresh seed provides five fictional accounts, three open requests, and examples of accepted, in-progress, completed, and cancelled rides. New registration, booking, and rating cases use the inputs in their own rows. Capture generated quote and ride IDs during the run. Start a fresh test database before cases that require original seed states.

## Entry criteria

- Dependencies are installed and Uvicorn starts against the isolated test database.
- The seed completes, `/health` returns `200`, and the application and `/docs` are reachable.
- Demo roles, initial ride statuses, and independent sessions are available for the selected cases.
- The tester has the workbook, expected requirement mappings, and a place to store sanitized evidence.

## Exit criteria

- Record a disposition for every in-scope case. Document a reason for any blocked or deferred case.
- Execute the checks for authorization, women-only eligibility, fixed fares, exclusive acceptance, trip states, and rating privacy before claiming readiness.
- Link each failure to a reproducible bug. Retest fixes against a fresh fixture and run relevant regression cases.
- Resolve critical and high defects before sign-off, or record explicit acceptance of the remaining risk.

## Risks and assumptions

| Risk or assumption | Test handling |
| --- | --- |
| Demo records change when a ride or verification is updated | Seed a new test file for cases that require original statuses. Use generated IDs only within the run that created them. |
| Two browser tabs often share a session | Separate roles by browser profile. Use `GET /api/auth/me` to confirm the active role before a server check. |
| A dashboard can display a snapshot from before another user's action | Refresh before checking the authoritative state. Preserve the unrefreshed screen when testing a stale acceptance attempt. |
| Quote expiry depends on server time | Use the returned UTC `expires_at`. Record the timestamp and the time of the attempted booking. |
| Manual race attempts may be sequential | Treat a late second request as a stale-state check. Repeat the race when timing evidence does not show overlap. |
| The dataset is small and fictional | Treat results as evidence for this lab build and fixture size. Record target browsers and viewports used. |

## Defect severity definitions

| Severity | Impact | CampusRide example |
| --- | --- | --- |
| S1 Critical | A core data integrity or access control rule fails | Two riders are assigned to a single request, or a student can approve rider applications. |
| S2 High | A primary workflow cannot complete or persists materially incorrect data | The ride starts after only one confirmation, or the booked fare changes. |
| S3 Medium | A workflow has a limited functional or usability impact with a practical workaround | A rejection message identifies the wrong field while invalid input is still refused. |
| S4 Low | A cosmetic or wording issue has little operational impact | A nonessential label is misaligned at one desktop width. |

Severity reflects impact. Priority reflects urgency. Use P0 for immediate action, P1 for the current fix cycle, P2 for a scheduled fix, and P3 for backlog consideration.

## Test execution strategy

1. Run TC-033 and inspect the freshly seeded admin totals in TC-030 before changing data.
2. Exercise registration, login, verification, and authorization. Run checks that assume a pending or unverified rider before changing that role, or reset the database.
3. Exercise quoting, booking, acceptance, restrictions, and cancellation. Use fresh fixtures for mutually exclusive state changes.
4. Verify each participant's view of start, completion, and rating disclosure. A fresh case can use the setup steps in its row or reuse the stated prerequisite when running a sequence.
5. Run the browser layout pass. Retest failed cases and related rules after any fix, then update the workbook with actual results and linked evidence.

A matching expected rejection is a Pass. Use Fail for an observed difference. Use Blocked when an attempted case cannot finish because a prerequisite failed. Leave unexecuted cases as Not Run. Source inspection and previous automated results are background for the design.
