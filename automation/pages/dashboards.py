from playwright.sync_api import Locator, Page

from automation.pages.booking import BookingPage


def _ride_card(section: Locator, ride_id: int) -> Locator:
    return section.get_by_test_id("ride-card").filter(
        has=section.page.get_by_text(f"Ride #{ride_id}", exact=True),
    )


class PassengerDashboard:
    def __init__(self, page: Page):
        self.page = page
        self.active = page.get_by_test_id("passenger-active")
        self.history = page.get_by_test_id("ride-history")

    def open(self) -> None:
        self.page.get_by_role("navigation", name="Dashboard").get_by_role("link", name="Passenger").click()

    def book(self) -> BookingPage:
        self.page.get_by_role("link", name="Book a ride").click()
        return BookingPage(self.page)

    def active_ride(self, ride_id: int) -> Locator:
        return _ride_card(self.active, ride_id)

    def past_ride(self, ride_id: int) -> Locator:
        return self.history.get_by_role("listitem").filter(
            has=self.page.get_by_role("link", name=f"View ride {ride_id}", exact=True),
        )


class RiderDashboard:
    def __init__(self, page: Page):
        self.page = page
        self.verification_status = page.get_by_test_id("rider-verification-status")
        self.available = page.get_by_test_id("available-rides")

    def open(self) -> None:
        self.page.get_by_role("navigation", name="Dashboard").get_by_role("link", name="Rider").click()

    def available_ride(self, ride_id: int) -> Locator:
        return _ride_card(self.available, ride_id)


class AdminDashboard:
    def __init__(self, page: Page):
        self.page = page

    def pending_review(self, email: str) -> Locator:
        return self.page.get_by_test_id("verification-row").filter(has=self.page.get_by_text(email, exact=True))

    def student(self, email: str) -> Locator:
        return self.page.get_by_test_id("student-accounts").get_by_role("row").filter(
            has=self.page.get_by_text(email, exact=True),
        )
