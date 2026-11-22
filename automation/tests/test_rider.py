from playwright.sync_api import expect

from app.demo import DEMO_ACCOUNTS
from automation.pages.dashboards import RiderDashboard
from automation.pages.ride_details import RideDetailsPage

REGULAR_REQUEST = 7
WOMEN_ONLY_REQUEST = 6


def test_approved_rider_accepts_an_available_request(sign_in):
    page = sign_in("tariq")
    dashboard = RiderDashboard(page)
    expect(dashboard.verification_status).to_have_text("Approved")

    dashboard.available_ride(REGULAR_REQUEST).get_by_test_id("accept-ride").click()

    expect(page).to_have_url(f"/rides/{REGULAR_REQUEST}")
    ride = RideDetailsPage(page)
    expect(ride.status).to_have_text("Accepted")
    expect(ride.summary.get_by_text(DEMO_ACCOUNTS["tariq"].name, exact=True)).to_be_visible()


def test_unverified_rider_has_no_acceptance_controls(sign_in):
    page = sign_in("mira")
    dashboard = RiderDashboard(page)
    dashboard.open()

    expect(page).to_have_url("/rider")
    expect(dashboard.verification_status).to_have_text("Unverified")
    expect(page.get_by_test_id("verification-form")).to_be_visible()
    expect(dashboard.available).to_have_count(0)
    expect(page.get_by_test_id("accept-ride")).to_have_count(0)


def test_second_rider_cannot_accept_from_a_stale_listing(sign_in):
    tariq = RiderDashboard(sign_in("tariq"))
    anika = RiderDashboard(sign_in("anika"))
    stale_card = anika.available_ride(REGULAR_REQUEST)
    expect(stale_card).to_be_visible()

    tariq.available_ride(REGULAR_REQUEST).get_by_test_id("accept-ride").click()
    expect(tariq.page).to_have_url(f"/rides/{REGULAR_REQUEST}")
    assigned_ride = RideDetailsPage(tariq.page)
    expect(assigned_ride.status).to_have_text("Accepted")

    stale_card.get_by_test_id("accept-ride").click()
    expect(stale_card.get_by_role("alert")).to_be_visible()
    expect(stale_card.get_by_role("alert")).to_have_text("This ride is no longer available.")
    expect(anika.page).to_have_url("/rider")

    anika.page.reload()
    expect(stale_card).to_have_count(0)
    tariq.page.reload()
    expect(assigned_ride.status).to_have_text("Accepted")
    expect(assigned_ride.summary.get_by_text(DEMO_ACCOUNTS["tariq"].name, exact=True)).to_be_visible()
    expect(assigned_ride.summary.get_by_text(DEMO_ACCOUNTS["anika"].name, exact=True)).to_have_count(0)


def test_only_eligible_rider_sees_a_women_only_request(sign_in):
    anika = RiderDashboard(sign_in("anika"))
    tariq = RiderDashboard(sign_in("tariq"))

    expect(anika.available_ride(REGULAR_REQUEST)).to_be_visible()
    expect(tariq.available_ride(REGULAR_REQUEST)).to_be_visible()
    restricted = anika.available_ride(WOMEN_ONLY_REQUEST)
    expect(restricted).to_be_visible()
    expect(restricted.get_by_text("Women-only", exact=True)).to_be_visible()
    expect(tariq.available_ride(WOMEN_ONLY_REQUEST)).to_have_count(0)
