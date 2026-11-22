from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.email = page.get_by_label("Campus email")
        self.password = page.get_by_label("Password", exact=True)
        self.submit = page.get_by_role("button", name="Sign in", exact=True)
        self.error = page.get_by_test_id("login-form").get_by_role("alert")

    def open(self) -> None:
        self.page.goto("/login")

    def sign_in(self, email: str, password: str) -> None:
        self.email.fill(email)
        self.password.fill(password)
        self.submit.click()
