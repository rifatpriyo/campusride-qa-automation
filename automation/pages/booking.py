import re

from playwright.sync_api import Page, expect

from app.domain import Preference, Stop
from automation.pages.ride_details import RideDetailsPage


class BookingPage:
    def __init__(self, page: Page):
        self.page = page
        self.pickup = page.get_by_label("Pickup location")
        self.destination = page.get_by_label("Destination")
        self.preference = page.get_by_label("Ride preference")
        self.quote_button = page.get_by_role("button", name="Get fare quote")
        self.confirm_button = page.get_by_role("button", name="Confirm booking")
        self.fare = page.get_by_test_id("quoted-fare")
        self.error = page.get_by_test_id("booking-form").get_by_role("alert")

    def choose_route(self, pickup: Stop, destination: Stop, preference: Preference = Preference.REGULAR) -> None:
        self.pickup.select_option(value=pickup.value)
        self.destination.select_option(value=destination.value)
        self.preference.select_option(value=preference.value)

    def confirm_booking(self) -> RideDetailsPage:
        self.confirm_button.click()
        expect(self.page).to_have_url(re.compile(r"/rides/\d+$"))
        return RideDetailsPage(self.page)
