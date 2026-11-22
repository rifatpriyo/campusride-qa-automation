from urllib.parse import urlsplit

from playwright.sync_api import Locator, Page


class RideDetailsPage:
    def __init__(self, page: Page):
        self.page = page
        self.summary = page.get_by_role("region", name="Ride summary")
        self.route = page.get_by_role("list", name="Ride route")
        self.status = page.get_by_test_id("ride-status")
        self.fare = page.get_by_test_id("confirmed-fare")
        self.start = page.get_by_test_id("confirm-start")
        self.complete = page.get_by_test_id("confirm-completion")
        self.ratings = page.get_by_test_id("ride-ratings")
        self.my_rating = self.ratings.get_by_test_id("my-rating")
        self.received_rating = self.ratings.get_by_test_id("received-rating")

    @property
    def ride_id(self) -> int:
        return int(urlsplit(self.page.url).path.rsplit("/", 1)[-1])

    def open(self, ride_id: int) -> None:
        self.page.goto(f"/rides/{ride_id}")

    def cancel(self) -> None:
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.page.get_by_test_id("cancel-ride").click()

    def confirmation(self, stage: str, participant: str) -> Locator:
        return self.page.get_by_test_id(f"{stage}-confirmations").get_by_role("listitem").filter(
            has=self.page.get_by_text(participant, exact=True),
        )

    def submit_rating(self, score: int) -> None:
        self.ratings.get_by_label("Rate your trip partner").select_option(value=str(score))
        self.ratings.get_by_role("button", name="Submit rating").click()
