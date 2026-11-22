from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.demo import DEMO_ACCOUNTS, DEMO_PASSWORD, seed_demo
from app.dependencies import SESSION_COOKIE
from app.models import Ride, User


def test_registration_validates_data_and_does_not_grant_roles(client, site):
    registration = {
        "name": "  Noor Test  ",
        "email": "  NOOR@campus.example ",
        "password": "NewCampus01!",
        "women_only_eligible": True,
    }
    response = client.post("/api/auth/register", json={**registration, "email": "noor@campus.example.org"})
    assert response.status_code == 422
    assert registration["password"] not in response.text
    assert client.post("/api/auth/register", json={**registration, "password": "NoDigitsHere"}).status_code == 422
    assert client.post("/api/auth/register", json={**registration, "is_admin": True}).status_code == 422

    response = client.post("/api/auth/register", json=registration)
    assert response.status_code == 201, response.text
    assert response.json() == {
        "id": response.json()["id"],
        "name": "Noor Test",
        "email": "noor@campus.example",
        "roles": ["passenger"],
        "women_only_eligible": True,
        "verification_status": None,
    }
    assert client.post("/api/auth/register", json=registration).status_code == 409
    with Session(site[0].state.engine) as db:
        password_hash = db.scalar(select(User.password_hash).where(User.email == "noor@campus.example"))
        assert password_hash is not None
        assert registration["password"] not in password_hash


def test_login_and_logout_invalidate_the_session(client):
    credentials = {"email": DEMO_ACCOUNTS["mira"].email, "password": DEMO_PASSWORD}
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={**credentials, "password": "Wrong123!"}).status_code == 401
    response = client.post("/api/auth/login", json=credentials)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    token = client.cookies.get(SESSION_COOKIE)
    assert client.get("/api/auth/me").json()["email"] == credentials["email"]
    assert client.post("/api/auth/logout", headers={"Origin": "https://other.example"}).status_code == 403
    assert client.post("/api/auth/logout").status_code == 204
    response = client.get("/api/auth/me", headers={"Cookie": f"{SESSION_COOKIE}={token}"})
    assert response.status_code == 401


def test_rider_rejection_resubmission_and_approval(sign_in):
    student, admin = sign_in("sami"), sign_in("admin")
    student_id = student.get("/api/auth/me").json()["id"]
    review = f"/api/admin/verifications/{student_id}/decision"
    available_ride_id = 7

    assert student.get("/api/rides/available").status_code == 403
    assert student.post(f"/api/rides/{available_ride_id}/accept").status_code == 403
    assert student.get("/api/admin/dashboard").status_code == 403
    assert student.post(review, json={"status": "approved"}).status_code == 403
    assert student.post("/api/rider/verification", json={"mock_reference": "MOCK-DEMO01"}).status_code == 409

    rejected = admin.post(review, json={"status": "rejected"})
    assert rejected.json()["status"] == "rejected"
    assert student.get("/api/rider/verification").json()["status"] == "rejected"
    assert student.post("/api/rider/verification", json={"mock_reference": "invalid"}).status_code == 422
    submitted = student.post("/api/rider/verification", json={"mock_reference": "MOCK-RETRY01"})
    assert submitted.status_code == 201
    assert submitted.json()["status"] == "pending"

    approved = admin.post(review, json={"status": "approved"})
    assert approved.json()["status"] == "approved"
    assert admin.post(review, json={"status": "rejected"}).status_code == 409
    assert student.get("/api/auth/me").json()["roles"] == ["passenger", "rider"]
    assert student.post(f"/api/rides/{available_ride_id}/accept").status_code == 200
    assert student.post("/api/rides/quote", json={
        "pickup": "north_gate", "destination": "main_library", "preference": "regular",
    }).status_code == 201


def test_admin_dashboard_and_demo_seed_are_repeatable(site, sign_in):
    admin, student = sign_in("admin"), sign_in("mira")
    assert student.get("/api/admin/dashboard").status_code == 403
    result = admin.get("/api/admin/dashboard")
    assert result.status_code == 200
    data = result.json()
    assert data["stats"]["students"] == 4
    assert data["stats"]["approved_riders"] == 2
    assert data["stats"]["pending_verifications"] == 1
    assert data["stats"]["rides_by_status"]["requested"] == 3
    assert data["pending_verifications"][0]["email"] == DEMO_ACCOUNTS["sami"].email
    assert "password_hash" not in result.text
    assert admin.get("/api/rides/available").status_code == 403
    assert student.get("/admin").status_code == 403
    assert "Rider verification request not found" in admin.post(
        "/api/admin/verifications/999/decision", json={"status": "approved"}
    ).text

    with Session(site[0].state.engine) as db:
        assert not seed_demo(db)
        assert db.scalar(select(func.count()).select_from(User)) == len(DEMO_ACCOUNTS)
        assert db.scalar(select(func.count()).select_from(Ride)) == 7
