from playwright.sync_api import expect

from app.demo import DEMO_ACCOUNTS
from automation.pages.login import LoginPage


def test_student_signs_in_with_valid_credentials(sign_in):
    page = sign_in("mira")

    expect(page.get_by_role("heading", name="My rides", exact=True)).to_be_visible()
    expect(page.get_by_text(DEMO_ACCOUNTS["mira"].name, exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Sign out")).to_be_visible()


def test_student_sees_error_for_invalid_credentials(open_page):
    page = open_page()
    login = LoginPage(page)
    login.open()

    login.sign_in(DEMO_ACCOUNTS["mira"].email, "IncorrectDemo456!")

    expect(login.error).to_be_visible()
    expect(login.error).to_have_text("Email or password is incorrect.")
    expect(page).to_have_url("/login")
    expect(page.get_by_role("button", name="Sign out")).to_have_count(0)


def test_sign_in_requires_email_and_password(open_page):
    page = open_page()
    login = LoginPage(page)
    login.open()

    login.submit.click()
    expect(login.email).to_have_attribute("required", "")
    expect(login.email).to_be_focused()

    login.email.fill(DEMO_ACCOUNTS["mira"].email)
    login.submit.click()
    expect(login.password).to_have_attribute("required", "")
    expect(login.password).to_be_focused()
    expect(page).to_have_url("/login")


def test_sign_out_requires_authentication_on_return(sign_in):
    page = sign_in("mira")

    page.get_by_role("button", name="Sign out").click()
    expect(page).to_have_url("/login")
    expect(page.get_by_role("heading", name="Sign in", exact=True)).to_be_visible()

    page.goto("/passenger")
    expect(page).to_have_url("/login")
    expect(LoginPage(page).submit).to_be_visible()
