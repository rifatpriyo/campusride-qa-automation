"""These assertions always describe the corrected business rules."""

import pytest

from app.config import Settings


@pytest.fixture
def demo_bug_mode(pytestconfig):
    return pytestconfig.getoption("--bug-lab") and Settings.from_env().demo_bug_mode


def test_bug_001_requires_rider_approval(sign_in):
    unverified, passenger = sign_in("mira"), sign_in("anika")
    profile = unverified.get("/api/auth/me").json()
    assert profile["roles"] == ["passenger"] and profile["verification_status"] is None
    assert unverified.get("/api/rides/available").status_code == 403

    response = unverified.post("/api/rides/5/accept")
    detail = passenger.get("/api/rides/5")
    assert detail.status_code == 200
    stored = detail.json()
    assert (response.status_code, stored["status"], stored["rider_name"]) == (403, "requested", None), (
        f"BUG-001 acceptance returned HTTP {response.status_code}; ride status was "
        f"{stored['status']} with rider {stored['rider_name']!r}"
    )


def test_bug_002_preserves_the_booked_fare(sign_in):
    passenger = sign_in("mira")
    quote = passenger.post("/api/rides/quote", json={
        "pickup": "north_gate",
        "destination": "residence_quad",
        "preference": "regular",
    })
    assert quote.status_code == 201
    assert quote.json()["fare_bdt"] == 80
    booking = passenger.post("/api/rides", json={"quote_id": quote.json()["id"]})
    assert booking.status_code == 201
    assert booking.json()["fare_bdt"] == 80

    path = f"/api/rides/{booking.json()['id']}"
    edit = passenger.patch(f"{path}/fare", json={"fare_bdt": 5})
    detail = passenger.get(path)
    assert detail.status_code == 200
    fare = detail.json()["fare_bdt"]
    assert (edit.status_code, fare) == (404, 80), (
        f"BUG-002 fare edit returned HTTP {edit.status_code}; readback fare was {fare} BDT"
    )


def test_bug_003_keeps_a_single_rating_private(sign_in):
    passenger, rider = sign_in("sami"), sign_in("tariq")
    path = "/api/rides/3"
    assert rider.post(f"{path}/complete").json()["status"] == "in_progress"
    assert passenger.post(f"{path}/complete").json()["status"] == "completed"
    first_rating = passenger.post(f"{path}/rating", json={"score": 5})
    assert first_rating.status_code == 200
    assert first_rating.json()["my_rating"] == 5

    response = rider.get(path)
    assert response.status_code == 200
    detail = response.json()
    assert detail["my_rating"] is None
    assert detail["received_rating"] is None, (
        f"BUG-003 unrated participant received score {detail['received_rating']!r}"
    )

    second_rating = rider.post(f"{path}/rating", json={"score": 4})
    assert second_rating.status_code == 200
    assert second_rating.json()["received_rating"] == 5
    assert passenger.get(path).json()["received_rating"] == 4


def test_bug_004_omits_phone_from_ride_details(sign_in):
    rider, outsider = sign_in("tariq"), sign_in("sami")
    assert outsider.get("/api/rides/4").status_code == 404
    response = rider.get("/api/rides/4")
    assert response.status_code == 200
    detail = response.json()
    assert detail["passenger_name"] == "Mira Rahman"
    assert "passenger_phone" not in detail, (
        f"BUG-004 participant response contained passenger_phone={detail.get('passenger_phone')!r}"
    )
