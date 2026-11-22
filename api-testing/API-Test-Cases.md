# CampusRide API test cases

Run the Postman requests from top to bottom against a fresh seeded test database with defect mode off. The registration uses the fictional student address in the environment. Later steps use the new verification, quote, and ride IDs captured during that run.

Required response fields and types are checked against JSON schemas. Error responses are validated as either a string `detail` for service errors or a list of field issues for `422`. Select a case below by its stable ID and review its Postman assertions for additional business checks.

## 01 Health and authentication

| Case | Request | Actor | HTTP | Requirement | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| API-001 | `GET /health` | Anonymous | `200` | REQ-016 | Confirm the local server can respond. |
| API-002 | `GET /openapi.json` | Anonymous | `200` | REQ-016 | Confirm the normal schema has the quote endpoint and excludes the exercise-only fare route. |
| API-003 | `GET /api/auth/me` | Anonymous | `401` | REQ-002 | Verify that the profile requires authentication. |
| API-004 | `POST /api/auth/login` | Anonymous | `401` | REQ-002 | Reject incorrect credentials and withhold a session cookie. |
| API-005 | `POST /api/auth/register` | Anonymous | `422` | REQ-001 | Require a campus-domain email without returning submitted credential data. |
| API-006 | `POST /api/auth/register` | Anonymous | `201` | REQ-001, REQ-003 | Create a passenger account with no verification record. |
| API-007 | `POST /api/auth/register` | Anonymous | `409` | REQ-001 | Reject a second registration for the same campus address. |
| API-008 | `POST /api/auth/login` | Anonymous | `200` | REQ-002, REQ-003 | Authenticate student and save the run-scoped HTTP-only cookie. |
| API-009 | `POST /api/auth/login` | Anonymous | `200` | REQ-002, REQ-003 | Authenticate mira and save the run-scoped HTTP-only cookie. |
| API-010 | `POST /api/auth/login` | Anonymous | `200` | REQ-002, REQ-003 | Authenticate tariq and save the run-scoped HTTP-only cookie. |
| API-011 | `POST /api/auth/login` | Anonymous | `200` | REQ-002, REQ-003 | Authenticate anika and save the run-scoped HTTP-only cookie. |
| API-012 | `POST /api/auth/login` | Anonymous | `200` | REQ-002, REQ-003 | Authenticate admin and save the run-scoped HTTP-only cookie. |

## 02 Verification and admin decisions

| Case | Request | Actor | HTTP | Requirement | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| API-013 | `GET /api/rider/verification` | student | `200` | REQ-004 | Read JSON null before the first submission. |
| API-014 | `POST /api/rider/verification` | student | `422` | REQ-004 | Validate the required mock-reference format. |
| API-015 | `POST /api/rider/verification` | student | `201` | REQ-004 | Create a pending verification request. |
| API-016 | `POST /api/admin/verifications/{student_id}/decision` | student | `403` | REQ-003, REQ-013 | Reject a review decision by a student. |
| API-017 | `GET /api/admin/dashboard` | student | `403` | REQ-003, REQ-013 | Restrict dashboard accounts and statistics to admins. |
| API-018 | `GET /api/admin/dashboard` | admin | `200` | REQ-013, REQ-014 | Read the dashboard and locate the same student's pending request. |
| API-019 | `POST /api/admin/verifications/{student_id}/decision` | admin | `200` | REQ-004, REQ-013 | Record a rejection for an existing pending request. |
| API-020 | `POST /api/rider/verification` | student | `201` | REQ-004 | Replace a rejected verification with a new pending request. |
| API-021 | `POST /api/admin/verifications/{student_id}/decision` | admin | `200` | REQ-004, REQ-013 | Approve the pending resubmission. |
| API-022 | `POST /api/admin/verifications/{student_id}/decision` | admin | `409` | REQ-004, REQ-013 | Reject a further decision on a reviewed request. |
| API-023 | `GET /api/auth/me` | student | `200` | REQ-003, REQ-004 | Verify both roles are available from the same student session. |

## 03 Quote, book and assign a regular ride

| Case | Request | Actor | HTTP | Requirement | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| API-024 | `POST /api/rides/quote` | mira | `422` | REQ-005 | Reject a route with the same pickup and destination. |
| API-025 | `POST /api/rides/quote` | mira | `201` | REQ-005, REQ-006 | Quote North Gate to Residence Quad at 80 BDT. |
| API-026 | `POST /api/rides` | anika | `404` | REQ-006 | Prevent Anika from redeeming Mira's quote. |
| API-027 | `POST /api/rides` | mira | `422` | REQ-006 | Reject the extra fare field on a booking. |
| API-028 | `POST /api/rides` | mira | `201` | REQ-003, REQ-006 | Redeem the quote once and capture the new ride ID. |
| API-029 | `POST /api/rides` | mira | `409` | REQ-006 | Reject a second booking from the same quote. |
| API-030 | `GET /api/rides` | mira | `200` | REQ-003, REQ-014 | List the passenger's own rides with summary fields only. |
| API-031 | `GET /api/rides/available` | tariq | `200` | REQ-004, REQ-007, REQ-014 | List eligible requests with an allowlist of public fields. |
| API-032 | `GET /api/rides/available` | mira | `403` | REQ-004 | Enforce rider approval for listing. |
| API-033 | `POST /api/rides/5/accept` | mira | `403` | REQ-004 | Check the approval guard on a different passenger's seeded open regular ride. |
| API-034 | `GET /api/rides/{ride_id}` | anika | `404` | REQ-014 | Hide participant details from an unrelated approved rider. |
| API-035 | `POST /api/rides/{ride_id}/accept` | tariq | `200` | REQ-006, REQ-007, REQ-008 | Assign the rider and preserve the price. |
| API-036 | `POST /api/rides/{ride_id}/accept` | anika | `409` | REQ-008 | Reject Anika's sequential acceptance after Tariq has claimed the ride. |

## 04 Trip confirmations and rating disclosure

| Case | Request | Actor | HTTP | Requirement | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| API-037 | `POST /api/rides/{ride_id}/complete` | tariq | `409` | REQ-011 | Prevent completion while the ride is still accepted. |
| API-038 | `POST /api/rides/{ride_id}/start` | mira | `200` | REQ-010 | Record the first start confirmation without starting the trip. |
| API-039 | `POST /api/rides/{ride_id}/start` | tariq | `200` | REQ-010 | Move the ride into progress after both start confirmations. |
| API-040 | `POST /api/rides/{ride_id}/cancel` | mira | `409` | REQ-009 | Enforce the cancellation boundary after both confirmations. |
| API-041 | `POST /api/rides/{ride_id}/complete` | tariq | `200` | REQ-011 | Keep the trip in progress with just one completion. |
| API-042 | `POST /api/rides/{ride_id}/complete` | mira | `200` | REQ-006, REQ-011 | Complete the trip and preserve the original fare. |
| API-043 | `POST /api/rides/{ride_id}/rating` | mira | `422` | REQ-012 | Reject a score greater than five. |
| API-044 | `POST /api/rides/{ride_id}/rating` | mira | `200` | REQ-012 | Record the passenger's own score while the received score is empty. |
| API-045 | `GET /api/rides/{ride_id}` | tariq | `200` | REQ-012, REQ-014 | Hide both rating fields from the rider until they submit. |
| API-046 | `POST /api/rides/{ride_id}/rating` | tariq | `200` | REQ-012 | Reveal the received score after both submissions. |
| API-047 | `GET /api/rides/{ride_id}` | mira | `200` | REQ-006, REQ-012, REQ-014 | Read the received score and unchanged fare with the allowed detail fields. |
| API-048 | `GET /api/rides/{ride_id}` | admin | `200` | REQ-012, REQ-013, REQ-014 | Allow the admin to see trip state while withholding participant ratings. |
| API-049 | `POST /api/rides/{ride_id}/rating` | mira | `409` | REQ-012 | Prevent replacing a participant's submitted score. |

## 05 Women-only eligibility and cancellation

| Case | Request | Actor | HTTP | Requirement | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| API-050 | `POST /api/rides/quote` | tariq | `403` | REQ-007 | Reject the preference for Tariq's profile. |
| API-051 | `POST /api/rides/quote` | mira | `201` | REQ-005, REQ-007 | Allow Mira to quote the selected route at 70 BDT. |
| API-052 | `POST /api/rides` | mira | `201` | REQ-006, REQ-007 | Create an unassigned women-only ride at the quoted price. |
| API-053 | `GET /api/rides/available` | tariq | `200` | REQ-007, REQ-014 | Exclude the restricted request from Tariq's list. |
| API-054 | `GET /api/rides/available` | anika | `200` | REQ-007, REQ-014 | Include the same request in Anika's list. |
| API-055 | `POST /api/rides/{women_ride_id}/accept` | tariq | `403` | REQ-007 | Apply women-only restrictions even on a direct acceptance request. |
| API-056 | `POST /api/rides/{women_ride_id}/accept` | anika | `200` | REQ-006, REQ-007 | Record the eligible assignment and the original price. |
| API-057 | `POST /api/rides/{women_ride_id}/cancel` | anika | `200` | REQ-009 | Cancel the accepted trip before both start confirmations. |
| API-058 | `GET /api/rides/{women_ride_id}` | mira | `200` | REQ-009, REQ-014 | Read the persisted cancellation from the passenger's session. |
| API-059 | `POST /api/rides/{women_ride_id}/accept` | anika | `409` | REQ-008, REQ-009 | Keep the cancelled request unavailable for reassignment. |

## 06 Sign-out and revocation

| Case | Request | Actor | HTTP | Requirement | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| API-060 | `POST /api/auth/logout` | student | `204` | REQ-002 | Revoke the student session and expire the client cookie. |
| API-061 | `GET /api/auth/me` | student | `401` | REQ-002 | Use the old test cookie once to verify server-side invalidation. |

## Pytest cross-checks

| Priority | Automated checks | Boundary covered |
| --- | --- | --- |
| Rider approval | `test_bug_001_requires_rider_approval`, `test_rider_rejection_resubmission_and_approval` | Authorization is enforced when reading and accepting rides. A denied acceptance leaves the assignment untouched. |
| Fixed fare | `test_booking_requires_an_owned_quote_and_keeps_its_fare`, `test_expired_quote_cannot_be_booked`, `test_concurrent_redemption_creates_only_one_ride`, `test_bug_002_preserves_the_booked_fare` | Quote ownership, expiry, one-time redemption, and immutable price. |
| Exclusive acceptance | `test_only_one_rider_can_accept_concurrently`, `test_assigned_rider_cannot_replay_acceptance` | Competing riders and replay by the assigned rider. |
| Women-only rules | `test_listing_and_acceptance_require_explicit_eligibility` | Lists and writes enforce the same restrictions. A rejected assignment leaves the request unchanged. |
| Trip lifecycle | `test_trip_lifecycle_and_two_sided_rating_privacy`, `test_simultaneous_confirmations_finalize_each_stage`, `test_cancellation_is_allowed_until_the_trip_starts` | Both participants are required for state transitions. Cancellation and invalid actions respect the current state. |
| Ratings and privacy | `test_bug_003_keeps_a_single_rating_private`, `test_bug_004_omits_phone_from_ride_details`, `test_ride_detail_uses_the_privacy_allowlist_for_participants_and_admin` | Early disclosure, admin rating visibility, and unintended response fields. |
| Admin and input contract | `test_protected_routes_return_401_without_a_session`, `test_admin_review_distinguishes_invalid_missing_and_resolved_requests`, `test_invalid_body_has_a_structured_field_error`, `test_repeat_login_rotates_the_session` | Missing credentials, invalid data, review conflicts, and session rotation. |

The Postman acceptance check exercises the second request in sequence. Pytest supplies the two-client concurrency check with an in-process barrier.
