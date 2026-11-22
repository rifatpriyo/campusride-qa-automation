"""Controlled defects for the local CampusRide QA exercise."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import Field
from sqlalchemy import update

from .dependencies import CurrentUser, Db, require_same_origin_for_writes
from .domain import DomainError, RideStatus
from .models import Ride, User
from .schemas import Input, RideDetail
from .services import rides

LOOPBACK_ADDRESSES = {"127.0.0.1", "::1"}
LOOPBACK_HOSTS = LOOPBACK_ADDRESSES | {"localhost"}
MOCK_PASSENGER_PHONE = "000-000-0104"


def is_active(request: Request) -> bool:
    return (
        request.app.state.settings.demo_bug_mode
        and request.client is not None
        and request.client.host in LOOPBACK_ADDRESSES
        and request.url.hostname in LOOPBACK_HOSTS
    )


Active = Annotated[bool, Depends(is_active)]


def require_active(request: Request) -> None:
    if not is_active(request):
        raise DomainError(404, "Not found.")


router = APIRouter(
    prefix="/api",
    tags=["Controlled defect lab"],
    dependencies=[Depends(require_active), Depends(require_same_origin_for_writes)],
)


class FareChange(Input):
    fare_bdt: int = Field(strict=True, gt=0, le=10_000)


@router.patch("/rides/{ride_id}/fare")
def change_booked_fare(ride_id: int, data: FareChange, db: Db, user: CurrentUser) -> RideDetail:
    """BUG-002. Change the confirmed fare on the passenger's own open booking."""
    ride = rides.visible_ride(db, user, ride_id)
    if ride.passenger_id != user.id:
        raise DomainError(404, "Ride not found.")
    result = db.execute(
        update(Ride)
        .where(Ride.id == ride_id, Ride.status == RideStatus.REQUESTED, Ride.quote_id.is_not(None))
        .values(fare_bdt=data.fare_bdt)
    )
    if result.rowcount != 1:
        raise DomainError(409, "Select an open ride booked from a quote for this exercise.")
    db.commit()
    return rides.ride_detail(ride, user)


def detail_with_defects(ride: Ride, user: User, detail: RideDetail) -> RideDetail | JSONResponse:
    if user.id == ride.passenger_id:
        other_score = ride.rider_rating
    elif user.id == ride.rider_id:
        other_score = ride.passenger_rating
    else:
        return detail

    payload = detail.model_dump(mode="json")
    # BUG-003. This projection ignores whether the viewer has submitted a rating.
    payload["received_rating"] = other_score
    # BUG-004. Returning JSON directly exposes a synthetic field outside RideDetail.
    payload["passenger_phone"] = MOCK_PASSENGER_PHONE
    return JSONResponse(payload)
