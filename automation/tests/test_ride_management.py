import pytest
from playwright.sync_api import expect

from automation.pages.dashboards import PassengerDashboard
from automation.pages.ride_details import RideDetailsPage


@pytest.fixture
def started_trip(sign_in):
    passenger = RideDetailsPage(sign_in("sami"))
    rider = RideDetailsPage(sign_in("tariq"))
    passenger.open(3)
    rider.open(3)
    return passenger, rider


def test_passenger_cancellation_moves_ride_to_history(sign_in):
    page = sign_in("mira")
    dashboard = PassengerDashboard(page)
    ride_id = 7
    dashboard.active_ride(ride_id).get_by_role("link", name=f"View ride {ride_id}").click()
    ride = RideDetailsPage(page)
    expect(ride.status).to_have_text("Requested")

    ride.cancel()
    expect(ride.status).to_have_text("Cancelled")
    expect(page.get_by_test_id("cancel-ride")).to_have_count(0)

    dashboard.open()
    expect(dashboard.active_ride(ride_id)).to_have_count(0)
    expect(dashboard.past_ride(ride_id).get_by_text("Cancelled", exact=True)).to_be_visible()


def test_one_completion_confirmation_keeps_trip_in_progress(started_trip):
    passenger, rider = started_trip
    expect(rider.status).to_have_text("In progress")

    rider.complete.click()
    expect(rider.confirmation("completion", "Rider")).to_have_text("Rider Confirmed")
    expect(rider.confirmation("completion", "Passenger")).to_have_text("Passenger Waiting")
    expect(rider.status).to_have_text("In progress")

    passenger.page.reload()
    expect(passenger.confirmation("completion", "Rider")).to_have_text("Rider Confirmed")
    expect(passenger.status).to_have_text("In progress")
    expect(passenger.complete).to_be_visible()
    expect(passenger.ratings).to_have_count(0)


def test_trip_starts_and_completes_after_both_participants_confirm(sign_in):
    passenger = RideDetailsPage(sign_in("mira"))
    rider = RideDetailsPage(sign_in("tariq"))
    passenger.open(4)
    rider.open(4)
    expect(passenger.status).to_have_text("Accepted")

    passenger.start.click()
    expect(passenger.confirmation("start", "Passenger")).to_have_text("Passenger Confirmed")
    expect(passenger.status).to_have_text("Accepted")
    expect(passenger.complete).to_have_count(0)

    rider.page.reload()
    rider.start.click()
    expect(rider.status).to_have_text("In progress")
    expect(rider.confirmation("start", "Rider")).to_have_text("Rider Confirmed")

    passenger.page.reload()
    passenger.complete.click()
    expect(passenger.confirmation("completion", "Passenger")).to_have_text("Passenger Confirmed")
    expect(passenger.status).to_have_text("In progress")

    rider.page.reload()
    rider.complete.click()
    expect(rider.status).to_have_text("Completed")
    expect(rider.confirmation("completion", "Rider")).to_have_text("Rider Confirmed")

    passenger.page.reload()
    expect(passenger.status).to_have_text("Completed")
    expect(passenger.ratings).to_be_visible()


def test_partners_only_see_received_ratings_after_both_submit(started_trip):
    passenger, rider = started_trip
    passenger.complete.click()
    expect(passenger.confirmation("completion", "Passenger")).to_have_text("Passenger Confirmed")

    rider.page.reload()
    rider.complete.click()
    expect(rider.status).to_have_text("Completed")
    passenger.page.reload()

    passenger.submit_rating(5)
    expect(passenger.my_rating).to_have_text("5 / 5")
    expect(passenger.received_rating).to_have_count(0)

    rider.page.reload()
    expect(rider.ratings.get_by_text("Ratings are shared after both participants submit.")).to_be_visible()
    expect(rider.ratings.get_by_text("Rating received", exact=True)).to_have_count(0)
    expect(rider.received_rating).to_have_count(0)

    rider.submit_rating(4)
    expect(rider.my_rating).to_have_text("4 / 5")
    expect(rider.received_rating).to_have_text("5 / 5")

    passenger.page.reload()
    expect(passenger.received_rating).to_have_text("4 / 5")
