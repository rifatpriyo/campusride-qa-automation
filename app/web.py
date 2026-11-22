from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from .config import ROOT
from .demo import DEMO_ACCOUNTS, DEMO_PASSWORD
from .dependencies import CurrentUser, Db, Viewer
from .domain import Preference, RideStatus, Stop, VerificationStatus
from .models import User
from .services import accounts, admin, rides

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=ROOT / "app" / "templates")
templates.env.globals.update(
    status_label=lambda value: value.replace("_", " ").capitalize(),
    preference_label=lambda value: "Women-only" if value == Preference.WOMEN_ONLY else "Regular",
)
FINISHED = {RideStatus.COMPLETED, RideStatus.CANCELLED}


def render(request: Request, name: str, *, status_code: int = 200, **context) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name=name, context={"status_code": status_code, **context}, status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _home_for(viewer: User | None) -> str:
    if viewer is None:
        return "/login"
    return "/admin" if viewer.is_admin else "/passenger"


@router.get("/")
def home(viewer: Viewer):
    return RedirectResponse(_home_for(viewer), status_code=303)


@router.get("/login")
def login(request: Request, db: Db, viewer: Viewer):
    if viewer:
        return RedirectResponse(_home_for(viewer), status_code=303)
    seeded = db.scalar(select(User.id).where(User.email == DEMO_ACCOUNTS["admin"].email, User.is_admin))
    demo_accounts = []
    if seeded:
        demo_accounts = [
            ("Passenger", DEMO_ACCOUNTS["mira"]),
            ("Rider", DEMO_ACCOUNTS["anika"]),
            ("Admin", DEMO_ACCOUNTS["admin"]),
        ]
    return render(
        request, "auth.html", form="login", demo_accounts=demo_accounts, demo_password=DEMO_PASSWORD,
        registered=request.query_params.get("registered") == "1",
    )


@router.get("/register")
def register(request: Request, viewer: Viewer):
    if viewer:
        return RedirectResponse(_home_for(viewer), status_code=303)
    return render(request, "auth.html", form="register")


@router.get("/passenger")
def passenger_dashboard(request: Request, db: Db, user: CurrentUser):
    passenger_rides = [ride for ride in rides.user_rides(db, user) if ride.passenger_id == user.id]
    return render(
        request, "passenger.html", page="passenger",
        active=[ride for ride in passenger_rides if ride.status not in FINISHED],
        history=[ride for ride in passenger_rides if ride.status in FINISHED],
    )


@router.get("/rider")
def rider_dashboard(request: Request, db: Db, user: CurrentUser):
    verification = accounts.verification_for(db, user)
    approved = verification is not None and verification.status == VerificationStatus.APPROVED
    assigned = [ride for ride in rides.user_rides(db, user) if ride.rider_id == user.id]
    return render(
        request, "rider.html", page="rider", verification=verification, approved=approved,
        available=rides.available_rides(db, user) if approved else [],
        active=[ride for ride in assigned if ride.status not in FINISHED],
        history=[ride for ride in assigned if ride.status in FINISHED],
    )


@router.get("/book")
def booking_form(request: Request, user: CurrentUser):
    accounts.require_student(user)
    return render(request, "booking.html", page="passenger", stops=list(Stop))


@router.get("/rides/{ride_id}")
def ride_status(request: Request, db: Db, user: CurrentUser, ride_id: int):
    ride = rides.visible_ride(db, user, ride_id, allow_admin=True)
    is_passenger = user.id == ride.passenger_id
    page = "admin" if user.is_admin else ("passenger" if is_passenger else "rider")
    details = rides.ride_detail(ride, user)
    return render(
        request, "ride.html", page=page, ride=details,
        can_cancel=not user.is_admin and ride.status in {RideStatus.REQUESTED, RideStatus.ACCEPTED},
        can_start=not user.is_admin and ride.status == RideStatus.ACCEPTED
        and not (ride.passenger_started if is_passenger else ride.rider_started),
        can_complete=not user.is_admin and ride.status == RideStatus.IN_PROGRESS
        and not (ride.passenger_completed if is_passenger else ride.rider_completed),
        can_rate=not user.is_admin and ride.status == RideStatus.COMPLETED and details.my_rating is None,
    )


@router.get("/admin")
def admin_dashboard(request: Request, db: Db, user: CurrentUser):
    return render(request, "admin.html", page="admin", dashboard=admin.dashboard(db, user))
