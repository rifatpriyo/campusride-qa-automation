from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from . import bug_lab

from .dependencies import SESSION_COOKIE, CurrentUser, Db, SessionToken, require_same_origin_for_writes
from .models import Verification
from .schemas import (
    AdminDashboard,
    Booking,
    Login,
    QuoteView,
    RatingInput,
    Registration,
    RideDetail,
    RideRoute,
    RideSummary,
    StudentView,
    VerificationDecision,
    VerificationRequest,
    VerificationView,
)
from .services import accounts, admin, rides

router = APIRouter(prefix="/api", dependencies=[Depends(require_same_origin_for_writes)])


@router.post("/auth/register", status_code=201, tags=["Accounts"])
def register(data: Registration, db: Db) -> StudentView:
    return accounts.profile(accounts.register(db, data))


@router.post("/auth/login", tags=["Accounts"])
def login(data: Login, request: Request, response: Response, db: Db, token: SessionToken) -> StudentView:
    user, new_token = accounts.login(db, data, token)
    response.set_cookie(
        SESSION_COOKIE,
        new_token,
        httponly=True,
        samesite="lax",
        secure=request.app.state.settings.secure_cookie,
        max_age=int(accounts.SESSION_DURATION.total_seconds()),
    )
    return accounts.profile(user, db.get(Verification, user.id))


@router.post("/auth/logout", status_code=204, tags=["Accounts"])
def logout(request: Request, db: Db, token: SessionToken) -> Response:
    if token:
        accounts.logout(db, token)
    response = Response(status_code=204)
    response.delete_cookie(
        SESSION_COOKIE, httponly=True, samesite="lax", secure=request.app.state.settings.secure_cookie
    )
    return response


@router.get("/auth/me", tags=["Accounts"])
def me(db: Db, user: CurrentUser) -> StudentView:
    return accounts.profile(user, db.get(Verification, user.id))


@router.get("/rider/verification", tags=["Rider verification"])
def get_verification(db: Db, user: CurrentUser) -> VerificationView | None:
    request = accounts.verification_for(db, user)
    return VerificationView.model_validate(request) if request else None


@router.post("/rider/verification", status_code=201, tags=["Rider verification"])
def submit_verification(data: VerificationRequest, db: Db, user: CurrentUser) -> VerificationView:
    return VerificationView.model_validate(accounts.submit_verification(db, user, data))


@router.get("/rides", tags=["Rides"])
def my_rides(db: Db, user: CurrentUser) -> list[RideSummary]:
    return [RideSummary.model_validate(ride) for ride in rides.user_rides(db, user)]


@router.get("/rides/available", tags=["Rides"])
def available_rides(db: Db, user: CurrentUser) -> list[RideSummary]:
    return [RideSummary.model_validate(ride) for ride in rides.available_rides(db, user)]


@router.post("/rides/quote", status_code=201, tags=["Rides"])
def quote_ride(route: RideRoute, db: Db, user: CurrentUser) -> QuoteView:
    """Get the fixed fare and a quote ID before confirming a booking."""
    return QuoteView.model_validate(rides.quote_ride(db, user, route))


@router.post("/rides", status_code=201, tags=["Rides"])
def book_ride(data: Booking, db: Db, user: CurrentUser) -> RideDetail:
    """Book a ride using one unexpired quote from this passenger's account."""
    return rides.ride_detail(rides.book_ride(db, user, data.quote_id), user)


@router.get("/rides/{ride_id}", response_model=RideDetail, tags=["Rides"])
def ride_detail(ride_id: int, db: Db, user: CurrentUser, defect_mode: bug_lab.Active) -> RideDetail | JSONResponse:
    ride = rides.visible_ride(db, user, ride_id, allow_admin=True)
    detail = rides.ride_detail(ride, user)
    return bug_lab.detail_with_defects(ride, user, detail) if defect_mode else detail


@router.post("/rides/{ride_id}/accept", tags=["Rides"])
def accept_ride(ride_id: int, db: Db, user: CurrentUser, defect_mode: bug_lab.Active) -> RideDetail:
    return rides.ride_detail(rides.accept_ride(db, user, ride_id, defect_mode=defect_mode), user)


@router.post("/rides/{ride_id}/cancel", tags=["Rides"])
def cancel_ride(ride_id: int, db: Db, user: CurrentUser) -> RideDetail:
    return rides.ride_detail(rides.cancel_ride(db, user, ride_id), user)


@router.post("/rides/{ride_id}/start", tags=["Rides"])
def confirm_start(ride_id: int, db: Db, user: CurrentUser) -> RideDetail:
    return rides.ride_detail(rides.confirm_trip(db, user, ride_id, "start"), user)


@router.post("/rides/{ride_id}/complete", tags=["Rides"])
def confirm_completion(ride_id: int, db: Db, user: CurrentUser) -> RideDetail:
    return rides.ride_detail(rides.confirm_trip(db, user, ride_id, "complete"), user)


@router.post("/rides/{ride_id}/rating", tags=["Rides"])
def rate_ride(ride_id: int, data: RatingInput, db: Db, user: CurrentUser) -> RideDetail:
    return rides.ride_detail(rides.rate_ride(db, user, ride_id, data.score), user)


@router.get("/admin/dashboard", tags=["Admin"])
def admin_dashboard(db: Db, user: CurrentUser) -> AdminDashboard:
    return admin.dashboard(db, user)


@router.post("/admin/verifications/{user_id}/decision", tags=["Admin"])
def review_verification(
    user_id: int, data: VerificationDecision, db: Db, user: CurrentUser
) -> VerificationView:
    return VerificationView.model_validate(accounts.review_verification(db, user, user_id, data))
