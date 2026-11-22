# CampusRide REST API test plan

## Objective

Verify the existing FastAPI contract in normal mode. Check both the response and persisted state where an action changes a ride, a verification, or a session. Use the [implemented requirements](../docs/REQUIREMENTS.md) and the local OpenAPI document as the test basis.

## Scope and test methods

| Area | Test focus |
| --- | --- |
| Authentication and authorization | Campus-only registration, duplicate accounts, sign-in, session cookie attributes, session rotation and revocation, and anonymous versus authenticated denials |
| Verification and admin | Mock reference format, pending and rejected states, resubmission, admin-only decisions, and status conflicts after a decision |
| Booking and fare | Quote amount, ownership, expiry, single redemption, and fare preservation through acceptance and completion |
| Eligibility and assignment | Unapproved and ineligible rider denials, women-only filtering, successful assignment, duplicate acceptance, and competing requests |
| Trip lifecycle | Independent start and completion confirmations, cancellation boundary, and invalid transitions |
| Ratings and privacy | Integer score validation, one rating per participant, disclosure only after both submit, admin rating visibility, and response field allowlists |

The Postman collection exercises the HTTP boundary in one ordered run. Pytest verifies independent business invariants with FastAPI TestClient. Its two-client tests cover competing acceptance, quote redemption, and trip confirmation using in-process requests. Phase 4 focuses on the local JSON API.

## Environment and data

- Serve Postman requests on loopback with `DEMO_BUG_MODE=false` and a newly seeded SQLite file. The environment file contains only fictional campus credentials.
- Give each Postman actor an explicit session cookie. Keep captured cookies and IDs in run-scoped variables. Requests reuse the IDs returned by the preceding steps.
- Pytest creates one seeded database per test session and copies it to a temporary file per test. Authenticated actors have separate clients.
- The collection expects the fresh seed in the [manual execution guide](../manual-testing/Execution-Guide.md#demo-accounts-and-rides). It additionally registers one test student, creates a regular ride and a women-only ride, and exercises decisions and lifecycle actions on those records.

## Response contract

| HTTP | Expectation |
| --- | --- |
| `200` | A successful read or permitted state change returns the documented JSON fields and types. A student with no verification receives JSON `null` from the verification read. |
| `201` | Registration, verification submission, quote creation, and booking return the newly created record. |
| `204` | Logout returns an empty body and clears the session cookie. |
| `401` | Missing, revoked, or invalid authentication. An incorrect password also returns `401`. |
| `403` | The session exists, and the actor lacks the role, approval, or eligibility required by the action. |
| `404` | The record is missing or hidden from the actor, such as an unrelated ride or someone else's quote. |
| `409` | The request conflicts with a stored state or uniqueness rule, such as a used quote or an already assigned ride. |
| `422` | Input fails validation. The response contains structured field issues. |

Service errors return a string `detail`. Validation errors return a list whose items contain `loc`, `msg`, and `type`. Read responses are checked for contact fields, credential hashes, and session secrets. Account email is expected in account responses and the authorized admin dashboard.

## Execution and acceptance

1. Start a fresh seeded Postman sandbox and run the health and normal-mode checks first.
2. Run every collection folder in order for one iteration. Verify that all requests executed. Inspect the precise expected outcome in the [test cases](API-Test-Cases.md) when an assertion fails.
3. Run the complete Pytest suite in normal mode. Review any failure against the requirement and actual response before classifying it as a product defect or setup issue.
4. Record passing, failing, and skipped totals separately for each runner. Treat an expected error response as a pass only when its status, shape, and business effect match the case.

The exit target is a complete run with every expected assertion satisfied. Stability risks include reusing a modified seed, sharing actor cookies, using an expired quote, and running a dependent folder without its setup steps. The [run and reset guide](README.md) describes the recovery steps.
