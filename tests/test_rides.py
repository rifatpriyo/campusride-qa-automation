from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest

from app.services import rides

ROUTE = {"pickup": "north_gate", "destination": "residence_quad", "preference": "regular"}


def quote(client, **changes):
    response = client.post("/api/rides/quote", json={**ROUTE, **changes})
    assert response.status_code == 201, response.text
    return response.json()


def book(client, **changes):
    fare = quote(client, **changes)
    response = client.post("/api/rides", json={"quote_id": fare["id"]})
    assert response.status_code == 201, response.text
    return response.json()


def post_together(path, first, second, **request_options):
    barrier = Barrier(2, timeout=5)

    def post(client):
        barrier.wait()
        return client.post(path, **request_options)

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(post, (first, second)))


@pytest.mark.parametrize("changes", [
    {"destination": "north_gate"},
    {"pickup": "unknown_stop"},
    {"preference": "invalid"},
])
def test_quote_validates_the_route(sign_in, changes):
    student = sign_in("mira")
    assert student.post("/api/rides/quote", json={**ROUTE, **changes}).status_code == 422


def test_booking_requires_an_owned_quote_and_keeps_its_fare(sign_in, monkeypatch):
    passenger, rider = sign_in("mira"), sign_in("tariq")
    result = quote(passenger)
    assert result["fare_bdt"] == 80
    assert rider.post("/api/rides", json={"quote_id": result["id"]}).status_code == 404
    assert passenger.post("/api/rides", json={"quote_id": result["id"], "fare_bdt": 1}).status_code == 422

    monkeypatch.setattr(rides, "fare_for", lambda pickup, destination: 999)
    booked = passenger.post("/api/rides", json={"quote_id": result["id"]})
    assert booked.status_code == 201
    assert booked.json()["fare_bdt"] == 80
    assert booked.json()["status"] == "requested"
    assert passenger.post("/api/rides", json={"quote_id": result["id"]}).status_code == 409
    accepted = rider.post(f"/api/rides/{booked.json()['id']}/accept")
    assert accepted.json()["fare_bdt"] == 80


def test_expired_quote_cannot_be_booked(sign_in, monkeypatch):
    passenger = sign_in("mira")
    result = quote(passenger)
    future = rides.utc_now() + timedelta(minutes=11)
    monkeypatch.setattr(rides, "utc_now", lambda: future)
    assert passenger.post("/api/rides", json={"quote_id": result["id"]}).status_code == 409


def test_concurrent_redemption_creates_only_one_ride(sign_in):
    first, second = sign_in("mira"), sign_in("mira")
    before = {ride["id"] for ride in first.get("/api/rides").json()}
    saved_quote = quote(first)
    responses = post_together("/api/rides", first, second, json={"quote_id": saved_quote["id"]})

    assert sorted(response.status_code for response in responses) == [201, 409]
    booked = next(response.json() for response in responses if response.status_code == 201)
    after = {ride["id"] for ride in first.get("/api/rides").json()}
    assert after - before == {booked["id"]}
    assert booked["fare_bdt"] == saved_quote["fare_bdt"]


def test_listing_and_acceptance_require_explicit_eligibility(sign_in):
    passenger, regular_rider, eligible_rider = (sign_in(key) for key in ("mira", "tariq", "anika"))
    restricted = book(passenger, preference="women_only")
    ordinary = book(passenger)
    own = book(eligible_rider)

    regular = regular_rider.get("/api/rides/available").json()
    eligible = eligible_rider.get("/api/rides/available").json()
    assert ordinary["id"] in {ride["id"] for ride in regular}
    assert restricted["id"] not in {ride["id"] for ride in regular}
    assert restricted["id"] in {ride["id"] for ride in eligible}
    assert own["id"] not in {ride["id"] for ride in eligible}
    assert all(set(ride) == {"id", "pickup", "destination", "preference", "fare_bdt", "status", "created_at"}
               for ride in regular + eligible)
    assert regular_rider.post("/api/rides/quote", json={**ROUTE, "preference": "women_only"}).status_code == 403
    assert eligible_rider.post(f"/api/rides/{own['id']}/accept").status_code == 403
    assert regular_rider.post(f"/api/rides/{restricted['id']}/accept").status_code == 403
    untouched = passenger.get(f"/api/rides/{restricted['id']}").json()
    assert (untouched["status"], untouched["rider_name"]) == ("requested", None)
    assert eligible_rider.post(f"/api/rides/{restricted['id']}/accept").status_code == 200


def test_only_one_rider_can_accept_concurrently(sign_in):
    passenger, first, second = (sign_in(key) for key in ("mira", "tariq", "anika"))
    ride = book(passenger)
    path = f"/api/rides/{ride['id']}"
    results = post_together(f"{path}/accept", first, second)
    assert sorted(result.status_code for result in results) == [200, 409]
    winner = next(result.json() for result in results if result.status_code == 200)
    assert passenger.get(path).json()["rider_name"] == winner["rider_name"]


def test_assigned_rider_cannot_replay_acceptance(sign_in):
    passenger, rider = sign_in("mira"), sign_in("tariq")
    ride = book(passenger)
    path = f"/api/rides/{ride['id']}"

    assert rider.post(f"{path}/accept").status_code == 200
    assert rider.post(f"{path}/accept").status_code == 409
    detail = passenger.get(path).json()
    assert (detail["status"], detail["rider_name"], detail["fare_bdt"]) == (
        "accepted", "Tariq Hasan", ride["fare_bdt"],
    )


def test_trip_lifecycle_and_two_sided_rating_privacy(sign_in):
    passenger, rider, outsider, admin = (sign_in(key) for key in ("mira", "anika", "tariq", "admin"))
    ride = book(passenger)
    path = f"/api/rides/{ride['id']}"

    assert passenger.post(f"{path}/start").status_code == 409
    assert rider.post(f"{path}/accept").status_code == 200
    assert outsider.get(path).status_code == 404
    assert outsider.post(f"{path}/start").status_code == 404
    assert admin.post(f"{path}/cancel").status_code == 404
    assert rider.post(f"{path}/complete").status_code == 409
    assert passenger.post(f"{path}/rating", json={"score": 5}).status_code == 409

    first_start = passenger.post(f"{path}/start").json()
    assert first_start["status"] == "accepted"
    assert first_start["passenger_started"] and not first_start["rider_started"]
    assert passenger.post(f"{path}/start").status_code == 409
    assert rider.post(f"{path}/start").json()["status"] == "in_progress"
    assert passenger.post(f"{path}/cancel").status_code == 409

    first_completion = rider.post(f"{path}/complete").json()
    assert first_completion["status"] == "in_progress"
    assert first_completion["rider_completed"] and not first_completion["passenger_completed"]
    assert passenger.post(f"{path}/complete").json()["status"] == "completed"
    assert passenger.post(f"{path}/rating", json={"score": 6}).status_code == 422

    first_rating = passenger.post(f"{path}/rating", json={"score": 5}).json()
    assert first_rating["my_rating"] == 5
    assert first_rating["received_rating"] is None
    assert rider.get(path).json()["received_rating"] is None
    assert outsider.post(f"{path}/rating", json={"score": 1}).status_code == 404
    second_rating = rider.post(f"{path}/rating", json={"score": 4}).json()
    assert second_rating["received_rating"] == 5
    finished = passenger.get(path).json()
    assert finished["received_rating"] == 4
    assert finished["fare_bdt"] == ride["fare_bdt"] == 80
    admin_detail = admin.get(path).json()
    assert admin_detail["my_rating"] is None and admin_detail["received_rating"] is None
    assert passenger.post(f"{path}/rating", json={"score": 2}).status_code == 409


def test_simultaneous_confirmations_finalize_each_stage(sign_in):
    passenger, rider = sign_in("mira"), sign_in("tariq")
    ride = book(passenger)
    path = f"/api/rides/{ride['id']}"
    assert rider.post(f"{path}/accept").status_code == 200

    for action, expected in [("start", "in_progress"), ("complete", "completed")]:
        results = post_together(f"{path}/{action}", passenger, rider)
        assert [item.status_code for item in results] == [200, 200]
        assert passenger.get(path).json()["status"] == expected


def test_cancellation_is_allowed_until_the_trip_starts(sign_in):
    passenger, rider = sign_in("mira"), sign_in("tariq")
    requested = book(passenger)
    path = f"/api/rides/{requested['id']}"
    assert rider.post(f"{path}/cancel").status_code == 404
    assert passenger.post(f"{path}/cancel").json()["status"] == "cancelled"
    assert rider.post(f"{path}/accept").status_code == 409

    accepted = book(passenger)
    path = f"/api/rides/{accepted['id']}"
    assert rider.post(f"{path}/accept").status_code == 200
    assert passenger.post(f"{path}/start").json()["status"] == "accepted"
    assert rider.post(f"{path}/cancel").json()["status"] == "cancelled"
    assert rider.post(f"{path}/start").status_code == 409
