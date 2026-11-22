from playwright.sync_api import expect

from app.demo import DEMO_ACCOUNTS
from automation.pages.dashboards import AdminDashboard, RiderDashboard


def test_admin_approval_gives_pending_student_rider_access(sign_in):
    applicant = RiderDashboard(sign_in("sami"))
    applicant.open()
    expect(applicant.verification_status).to_have_text("Pending")
    expect(applicant.available).to_have_count(0)

    email = DEMO_ACCOUNTS["sami"].email
    admin = AdminDashboard(sign_in("admin"))
    admin.pending_review(email).get_by_role("button", name="Approve", exact=True).click()
    expect(admin.student(email).get_by_role("cell", name="Approved", exact=True)).to_be_visible()
    expect(admin.pending_review(email)).to_have_count(0)

    applicant.page.reload()
    expect(applicant.verification_status).to_have_text("Approved")
    expect(applicant.available_ride(7).get_by_test_id("accept-ride")).to_be_visible()


def test_student_cannot_open_admin_dashboard(sign_in):
    page = sign_in("mira")
    expect(page.get_by_role("navigation", name="Dashboard").get_by_role("link", name="Admin")).to_have_count(0)

    response = page.goto("/admin")

    assert response is not None and response.status == 403
    expect(page.get_by_role("heading", name="Unable to open this page")).to_be_visible()
    expect(page.get_by_role("alert")).to_have_text("This action requires an admin account.")
    expect(page.get_by_test_id("admin-stats")).to_have_count(0)
    expect(page.get_by_test_id("approve-rider")).to_have_count(0)
