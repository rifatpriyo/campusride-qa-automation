# CampusRide QA Lab Phase 1 requirements

| ID | Requirement | Acceptance criteria |
| --- | --- | --- |
| REQ-001 | Student registration | An account requires a unique `@campus.example` email. The server trims and lowercases the email. The password has 10–128 characters and includes a letter and a digit. Credentials are validated on the server. |
| REQ-002 | Session authentication | Sign-in sets an expiring HTTP-only session cookie. The database stores salted scrypt password hashes and hashed session tokens. Sign-out invalidates the current session. Protected APIs return `401` for anonymous callers. |
| REQ-003 | Roles | Registered students can book rides as passengers. Approval adds rider access while preserving passenger access. Only admin accounts can review riders and view the admin dashboard. |
| REQ-004 | Rider verification | A student submits a fictional `MOCK-` code. An admin can approve or reject a pending request. A rejected user can apply again. Browsing and acceptance require approval. |
| REQ-005 | Fare preview | A student chooses distinct stops and a regular or women-only preference. The server calculates and displays a deterministic fare in BDT before confirmation. |
| REQ-006 | Confirmed fare | A booking uses an unexpired, unused quote owned by the passenger. The ride copies the quoted route, preference, and fare. The fare stays fixed through later ride actions. |
| REQ-007 | Eligible listing and acceptance | Only available requests matching an approved rider's explicit test-profile eligibility are listed and can be accepted. A rider cannot accept their own request. Creating a women-only request also requires an eligible test profile. |
| REQ-008 | Exclusive acceptance | A requested ride can be assigned to one rider. Simultaneous eligible attempts produce one successful assignment and one `409` response. |
| REQ-009 | Cancellation | The requesting passenger can cancel an open ride. Either assigned participant can cancel an accepted ride before it starts. Cancelling a started or completed ride returns `409`. |
| REQ-010 | Start confirmations | The assigned rider and passenger independently confirm the start. The ride advances to `in_progress` only after both confirmations are recorded. |
| REQ-011 | Completion confirmations | The two participants independently confirm completion while the ride is in progress. The ride advances to `completed` only after both confirmations are recorded. |
| REQ-012 | Ratings | After completion, each participant can submit one integer rating from 1 to 5. A participant's received score becomes visible only after both ratings exist. |
| REQ-013 | Admin dashboard | An admin can list accounts, review pending requests, see all rides and their states, and view counts for students, approved riders, pending approvals, and each ride status. |
| REQ-014 | Privacy | Open ride listings contain only ride ID, stops, preference, fare, status, and creation time. Participant details are restricted to the participants and admins. The app uses fictional data and has no phone-number field. |
| REQ-015 | Browser workflows | The app includes responsive sign-in, registration, passenger, rider, booking, ride status, and admin pages. Key controls have stable `data-testid` attributes. |
| REQ-016 | Local setup | `GET /health` returns `200` with `{"status":"ok"}` on a working app. `/docs` serves interactive API documentation. Windows setup and the repeatable demo seed are documented in the README. |

The backend suite in [tests](../tests/) checks authentication and approvals, fare and ride rules, and route responses against an isolated database.
