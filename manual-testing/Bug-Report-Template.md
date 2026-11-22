# CampusRide QA Lab bug report

| Field | Entry |
| --- | --- |
| Bug ID | `BUG-___` |
| Title | `<module, action, and observed failure>` |
| Status | New |
| Severity | `<S1 Critical / S2 High / S3 Medium / S4 Low>` |
| Priority | `<P0 Immediate / P1 Current cycle / P2 Scheduled / P3 Backlog>` |
| Linked test case | `TC-___` |
| Linked requirement | `REQ-___` |

## Description

Describe the failure and its impact in one or two sentences. Record how often it occurred, such as 2 of 3 attempts.

## Environment

- App version and Git commit or build identifier
- OS, browser and version or HTTP client, and viewport if relevant
- Base URL and test database fixture or reset state
- Observation date, time, and time zone

## Preconditions

Specify the fictional account role, rider approval and eligibility state, ride or quote ID, starting status, and any second session required.

## Reproduction steps

1. Sign in as the specified test account.
2. Open the affected page or make the specified HTTP request.
3. Enter the exact test values and perform the action.
4. Capture the displayed result or HTTP response and any change to the stored state.

## Expected result

State the required UI outcome, response code, or final state. Point to the linked requirement or expected result from the case.

## Actual result

Record exactly what appeared or what was returned. Include the response code, error text, and resulting state when relevant.

## Evidence

Add a screenshot, redacted request and response, or timing capture. For competing requests, show both outcomes and the final assignment. Redact session tokens and credential hashes.

## Retest

Record the fix build, test date, fixture, result, and evidence. Update the status to Triaged, In Progress, Ready for Retest, Closed, or Reopened as appropriate. See the [severity definitions](Test-Plan.md#defect-severity-definitions).
