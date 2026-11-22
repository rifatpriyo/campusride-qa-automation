# CampusRide interview notes

CampusRide is an independent SQA portfolio project. It simulates students sharing rides on a fictional campus. I worked from written requirements, inspected the implemented pages and routes, and used fictional accounts to check the rules from several users' perspectives.

## A walkthrough I can give

I would start with a regular booking. A passenger chooses North Gate and Residence Quad. The page displays BDT 80 before confirmation. After booking, I check the saved route and fare, sign in as an approved rider, and accept the request. I would pause after the first participant confirms completion and show that the trip stays in progress. That point shows why I check intermediate states along with the final result. [Browser scenarios](../automation/tests/)

## Ten interview questions

### 1. What did you test, and why did you prioritize it?

I tested registration, sign-in, rider approval, fare quoting, booking, eligibility, acceptance, cancellation, trip confirmations and ratings. I prioritized mistakes that would affect another person. For example, two riders receiving the same assignment is more consequential than a minor layout issue. I linked the cases to the requirements so another tester could see what was covered. [Traceability matrix](../manual-testing/Traceability-Matrix.xlsx)

### 2. How did you choose test data for an input field?

I tested values on either side of a rule. A password must be 10 to 128 characters and include a letter and a digit. The manual workbook records checks at 9, 10, 128 and 129 characters, plus inputs missing a required character type. The boundaries help catch a comparison that wrongly accepts or rejects exactly one length. [Manual cases, TC-003](../manual-testing/Test-Cases.xlsx)

### 3. What is the difference between manual testing and automation here?

For a manual case, I follow written steps, observe the application or HTTP response, and record what actually happened. An automated test has code perform the steps and compare the outcome with an assertion. The workbook has 29 recorded passes and four cases still to run. Playwright can repeatedly check the fare preview, while a tester can judge whether a narrow layout is usable. The manual disposition belongs to the person executing that case. [QA summary](../reports/QA-Summary.md)

### 4. What does an API test check?

An API test sends a request directly to the backend and inspects the response. For a quote, I supply two valid stops and a preference, expect HTTP 201, check the numeric fare and capture the quote ID. The booking request uses that ID. Checking both the status and the saved result catches a server that accepts a request but stores the wrong price. [API cases, quote through assignment](../api-testing/API-Test-Cases.md)

### 5. Why do negative tests matter?

They show whether the app handles invalid input and refuses actions a user cannot take. A successful login says little about what happens when someone enters the wrong password. For an invalid route with identical stops, the expected outcome is a validation error. That negative case passes when the expected rejection appears and the booking cannot proceed.

### 6. How did you test a stale request and a race between two riders?

For the browser case, two approved riders open the same listing. After the first accepts, the second clicks the still-visible button and sees that the ride is unavailable. For the backend case, two signed-in clients wait at the same synchronization point, then send their acceptance requests. I check for one success and one conflict, then read the ride again to confirm the successful rider kept the assignment. [UI tests](../automation/tests/test_rider.py) · [Backend tests](../tests/test_rides.py)

### 7. How did you identify and report a defect?

I used four deliberately introduced local defects to practice investigation. One exercise changed a booked fare. The regression check compared the confirmed price with the saved amount and detected that difference. I recorded the expected rule, observed behavior, impact, evidence and verification status. The archived comparison shows the same assertion passing in normal mode. I describe this as a controlled exercise when discussing the project. [Fare defect report](../bug-reports/BUG-002.md) · [Comparison run](../reports/bug-lab/04-corrected-mode.txt)

### 8. How would you verify a rating privacy rule?

I would use two separate signed-in sessions for the participants in a completed trip. After the first submits a score, I would check each person's view. The author should see their own score and the other person should still be able to submit independently. After both submit, I would refresh both views and verify the received scores in the correct direction. Using different scores makes an accidental swap easy to spot. [Browser test](../automation/tests/test_ride_management.py)

### 9. How does GitHub Actions run the tests?

A push or pull request triggers three jobs on Ubuntu. One runs the Python backend tests, one seeds a local server for Newman, and one installs Chromium and runs Playwright. All three use normal demo behavior. A failed assertion makes its test command return a nonzero exit code. The other jobs can finish, and the workflow attempts to upload the available reports and browser failure evidence. I would use the hosted run's own result when describing CI status. [Workflow](../.github/workflows/qa-tests.yml)

### 10. What was the biggest challenge, and what would you do next?

Keeping the starting state repeatable was the hardest part. A cancellation, approval or rating changes what later users can do. The Pytest suites copy a seeded SQLite database for each case, and browser actors use separate sessions. The Postman collection uses captured IDs within one ordered run. I would next complete the outstanding responsive-layout and cancellation checks in the manual workbook and attach the observations. [Execution guide](../manual-testing/Execution-Guide.md) · [Automation fixtures](../automation/conftest.py)

## Resume bullets

- Designed 33 manual QA cases mapped to 16 requirements for a fictional student ride-sharing application and documented 29 executed cases.
- Built a Postman collection with 61 requests and 240 assertions and ran 32 backend and API regression tests against isolated SQLite data.
- Automated 18 Chromium scenarios with Python, Pytest and Playwright, including two-user assignment, trip confirmation and rating privacy checks.
