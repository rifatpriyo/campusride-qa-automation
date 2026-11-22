import pytest
from playwright.sync_api import expect

from app.domain import Stop
from automation.pages.dashboards import PassengerDashboard


@pytest.fixture
def booking(sign_in):
    return PassengerDashboard(sign_in("mira")).book()


@pytest.fixture
def booked_ride(booking):
    booking.choose_route(Stop.NORTH_GATE, Stop.RESIDENCE_QUAD)
    booking.quote_button.click()
    return booking.confirm_booking()


def test_passenger_requests_a_regular_ride(booked_ride):
    expect(booked_ride.status).to_have_text("Requested")
    expect(booked_ride.summary.get_by_text("Regular", exact=True)).to_be_visible()
    expect(booked_ride.route.get_by_role("listitem")).to_have_text([
        "Pickup North Gate", "Destination Residence Quad",
    ])
    expect(booked_ride.fare).to_have_text("BDT 80")


def test_booking_rejects_the_same_pickup_and_destination(booking):
    booking.choose_route(Stop.NORTH_GATE, Stop.NORTH_GATE)
    booking.quote_button.click()

    expect(booking.error).to_be_visible()
    expect(booking.error).to_contain_text("Choose a destination different from your pickup.")
    expect(booking.confirm_button).to_be_disabled()
    expect(booking.fare).to_be_hidden()
    expect(booking.page).to_have_url("/book")


def test_fare_is_shown_before_confirmation_and_requoted_after_route_change(booking):
    booking.choose_route(Stop.NORTH_GATE, Stop.RESIDENCE_QUAD)
    expect(booking.confirm_button).to_be_disabled()

    booking.quote_button.click()
    expect(booking.fare).to_be_visible()
    expect(booking.fare).to_have_text("BDT 80")
    expect(booking.confirm_button).to_be_enabled()
    expect(booking.page).to_have_url("/book")

    booking.destination.select_option(value=Stop.ENGINEERING_HALL.value)
    expect(booking.fare).to_be_hidden()
    expect(booking.confirm_button).to_be_disabled()
    booking.quote_button.click()
    expect(booking.fare).to_be_visible()
    expect(booking.fare).to_have_text("BDT 60")
    expect(booking.confirm_button).to_be_enabled()
    expect(booking.page).to_have_url("/book")


def test_new_booking_appears_on_passenger_dashboard(booked_ride):
    ride_id = booked_ride.ride_id
    dashboard = PassengerDashboard(booked_ride.page)
    dashboard.open()

    ride = dashboard.active_ride(ride_id)
    expect(ride).to_be_visible()
    expect(ride.get_by_text("Requested", exact=True)).to_be_visible()
    expect(ride.get_by_role("list", name="Ride route").get_by_role("listitem")).to_have_text([
        "Pickup North Gate", "Destination Residence Quad",
    ])
