import pytest

from app.demo import DEMO_ACCOUNTS, DEMO_PASSWORD
from app.dependencies import SESSION_COOKIE

DETAIL_FIELDS = {
    "id", "pickup", "destination", "preference", "fare_bdt", "status", "created_at",
    "passenger_name", "rider_name", "passenger_started", "rider_started",
    "passenger_completed", "rider_completed", "my_rating", "received_rating",
}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        pytest.param("GET", "/api/rides", None, id="list-my-rides"),
        pytest.param("POST", "/api/rides/quote", {
            "pickup": "north_gate", "destination": "main_library", "preference": "regular",
        }, id="quote-ride"),
        pytest.param("GET", "/api/admin/dashboard", None, id="admin-dashboard"),
        pytest.param("POST", "/api/admin/verifications/4/decision", {"status": "approved"}, id="admin-review"),
    ],
)
def test_protected_routes_return_401_without_a_session(client, method, path, payload):
    response = client.request(method, path, json=payload)
    assert response.status_code == 401
    assert response.json() == {"detail": "Sign in to continue."}


@pytest.mark.parametrize(
    ("path", "payload", "field"),
    [
        pytest.param("/api/rider/verification", {"mock_reference": "wrong"}, "mock_reference", id="mock-format"),
        pytest.param("/api/rides", {"quote_id": "not-a-quote"}, "quote_id", id="quote-id-format"),
        pytest.param("/api/rides/1/rating", {"score": "5"}, "score", id="integer-rating"),
    ],
)
def test_invalid_body_has_a_structured_field_error(sign_in, path, payload, field):
    response = sign_in("mira").post(path, json=payload)
    assert response.status_code == 422
    issues = response.json()["detail"]
    assert len(issues) == 1
    issue = issues[0]
    assert set(issue) == {"loc", "msg", "type"}
    assert issue["loc"] == ["body", field]
    assert isinstance(issue["msg"], str) and isinstance(issue["type"], str)


def test_repeat_login_rotates_the_session(client):
    credentials = {"email": DEMO_ACCOUNTS["mira"].email, "password": DEMO_PASSWORD}
    assert client.post("/api/auth/login", json=credentials).status_code == 200
    previous = client.cookies.get(SESSION_COOKIE)
    assert previous

    assert client.post("/api/auth/login", json=credentials).status_code == 200
    assert client.cookies.get(SESSION_COOKIE) and client.cookies.get(SESSION_COOKIE) != previous
    stale = client.get("/api/auth/me", headers={"Cookie": f"{SESSION_COOKIE}={previous}"})
    assert stale.status_code == 401
    current = client.get("/api/auth/me")
    assert current.status_code == 200
    assert current.json()["email"] == credentials["email"]


def test_admin_review_distinguishes_invalid_missing_and_resolved_requests(sign_in):
    admin, applicant = sign_in("admin"), sign_in("sami")
    applicant_id = applicant.get("/api/auth/me").json()["id"]
    path = f"/api/admin/verifications/{applicant_id}/decision"

    invalid = admin.post(path, json={"status": "pending"})
    assert invalid.status_code == 422
    assert invalid.json()["detail"][0]["loc"] == ["body", "status"]
    missing = admin.post("/api/admin/verifications/10000/decision", json={"status": "approved"})
    assert missing.status_code == 404
    approved = admin.post(path, json={"status": "approved"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert admin.post(path, json={"status": "rejected"}).status_code == 409
    assert applicant.get("/api/rider/verification").json()["status"] == "approved"


def test_ride_detail_uses_the_privacy_allowlist_for_participants_and_admin(sign_in):
    passenger, rider, admin = (sign_in(account) for account in ("mira", "anika", "admin"))
    for actor in (passenger, rider, admin):
        response = actor.get("/api/rides/1")
        assert response.status_code == 200
        body = response.json()
        assert set(body) == DETAIL_FIELDS
        assert (body["passenger_name"], body["rider_name"]) == ("Mira Rahman", "Anika Karim")
