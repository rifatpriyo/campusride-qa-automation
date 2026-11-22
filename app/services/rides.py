from datetime import timedelta
from typing import Literal
from uuid import uuid4

from sqlalchemy import and_, case, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..domain import DomainError, Preference, RideStatus, Stop, utc_now
from ..models import FareQuote, Ride, User
from ..schemas import RideDetail, RideRoute, RideSummary
from .accounts import require_rider, require_student

QUOTE_LIFETIME = timedelta(minutes=10)
STOP_ZONES = {stop: index for index, stop in enumerate(Stop)}


def fare_for(pickup: Stop, destination: Stop) -> int:
    return 40 + 10 * abs(STOP_ZONES[pickup] - STOP_ZONES[destination])


def _can_choose_preference(user: User, preference: Preference) -> bool:
    return preference == Preference.REGULAR or user.women_only_eligible


def quote_ride(db: Session, user: User, route: RideRoute) -> FareQuote:
    require_student(user)
    if not _can_choose_preference(user, route.preference):
        raise DomainError(403, "This test profile is ineligible for women-only rides.")
    quote = FareQuote(
        id=uuid4().hex,
        passenger_id=user.id,
        pickup=route.pickup,
        destination=route.destination,
        preference=route.preference,
        fare_bdt=fare_for(route.pickup, route.destination),
        expires_at=utc_now() + QUOTE_LIFETIME,
    )
    db.add(quote)
    db.commit()
    return quote


def book_ride(db: Session, user: User, quote_id: str) -> Ride:
    require_student(user)
    quote = db.get(FareQuote, quote_id)
    if quote is None or quote.passenger_id != user.id:
        raise DomainError(404, "Fare quote not found.")
    if quote.expires_at <= utc_now():
        raise DomainError(409, "This quote expired. Request a new fare quote.")
    if not _can_choose_preference(user, quote.preference):
        raise DomainError(403, "This test profile is ineligible for women-only rides.")

    ride = Ride(
        quote_id=quote.id,
        passenger_id=user.id,
        pickup=quote.pickup,
        destination=quote.destination,
        preference=quote.preference,
        fare_bdt=quote.fare_bdt,
        status=RideStatus.REQUESTED,
    )
    db.add(ride)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(Ride.id).where(Ride.quote_id == quote_id)) is not None:
            raise DomainError(409, "This quote was already used to book a ride.") from None
        raise
    return ride


def _available_conditions(user: User):
    conditions = [Ride.status == RideStatus.REQUESTED, Ride.rider_id.is_(None), Ride.passenger_id != user.id]
    if not user.women_only_eligible:
        conditions.append(Ride.preference == Preference.REGULAR)
    return conditions


def available_rides(db: Session, user: User) -> list[Ride]:
    require_rider(db, user)
    return list(db.scalars(select(Ride).where(*_available_conditions(user)).order_by(Ride.id.desc())))


def user_rides(db: Session, user: User) -> list[Ride]:
    require_student(user)
    return list(db.scalars(
        select(Ride)
        .where(or_(Ride.passenger_id == user.id, Ride.rider_id == user.id))
        .order_by(Ride.id.desc())
    ))


def _find_ride(db: Session, ride_id: int) -> Ride:
    ride = db.get(Ride, ride_id)
    if ride is None:
        raise DomainError(404, "Ride not found.")
    return ride


def visible_ride(db: Session, user: User, ride_id: int, *, allow_admin: bool = False) -> Ride:
    ride = _find_ride(db, ride_id)
    if user.id not in (ride.passenger_id, ride.rider_id) and not (allow_admin and user.is_admin):
        raise DomainError(404, "Ride not found.")
    return ride


def ride_detail(ride: Ride, user: User) -> RideDetail:
    my_rating = received_rating = None
    if user.id == ride.passenger_id:
        my_rating, received_rating = ride.passenger_rating, ride.rider_rating
    elif user.id == ride.rider_id:
        my_rating, received_rating = ride.rider_rating, ride.passenger_rating

    return RideDetail(
        **RideSummary.model_validate(ride).model_dump(),
        passenger_name=ride.passenger.name,
        rider_name=ride.rider.name if ride.rider else None,
        passenger_started=ride.passenger_started,
        rider_started=ride.rider_started,
        passenger_completed=ride.passenger_completed,
        rider_completed=ride.rider_completed,
        my_rating=my_rating,
        received_rating=received_rating if my_rating is not None else None,
    )


def _update_ride(db: Session, statement) -> bool:
    changed = db.execute(statement.execution_options(synchronize_session=False)).rowcount == 1
    if changed:
        db.commit()
    else:
        db.rollback()
    return changed


def accept_ride(db: Session, user: User, ride_id: int, *, defect_mode: bool = False) -> Ride:
    if defect_mode:
        # BUG-001. The lab branch checks student access in place of rider approval.
        require_student(user)
    else:
        require_rider(db, user)
    # The state and eligibility predicates are checked by the same write that assigns the rider.
    statement = (
        update(Ride)
        .where(Ride.id == ride_id, *_available_conditions(user))
        .values(rider_id=user.id, status=RideStatus.ACCEPTED)
    )
    if not _update_ride(db, statement):
        ride = _find_ride(db, ride_id)
        if ride.passenger_id == user.id:
            raise DomainError(403, "You cannot accept your own ride request.")
        if not _can_choose_preference(user, ride.preference):
            raise DomainError(403, "This test profile is ineligible for women-only rides.")
        raise DomainError(409, "This ride is no longer available.")
    return _find_ride(db, ride_id)


def cancel_ride(db: Session, user: User, ride_id: int) -> Ride:
    visible_ride(db, user, ride_id)
    statement = (
        update(Ride)
        .where(
            Ride.id == ride_id,
            or_(
                and_(Ride.status == RideStatus.REQUESTED, Ride.passenger_id == user.id),
                and_(
                    Ride.status == RideStatus.ACCEPTED,
                    or_(Ride.passenger_id == user.id, Ride.rider_id == user.id),
                ),
            ),
        )
        .values(status=RideStatus.CANCELLED)
    )
    if not _update_ride(db, statement):
        raise DomainError(409, "A ride can only be cancelled before it starts.")
    return _find_ride(db, ride_id)


def confirm_trip(
    db: Session, user: User, ride_id: int, step: Literal["start", "complete"]
) -> Ride:
    ride = visible_ride(db, user, ride_id)
    if step == "start":
        current, next_status = RideStatus.ACCEPTED, RideStatus.IN_PROGRESS
        passenger_flag, rider_flag = Ride.passenger_started, Ride.rider_started
    else:
        current, next_status = RideStatus.IN_PROGRESS, RideStatus.COMPLETED
        passenger_flag, rider_flag = Ride.passenger_completed, Ride.rider_completed

    if ride.passenger_id == user.id:
        participant, own_flag, other_flag = Ride.passenger_id, passenger_flag, rider_flag
    else:
        participant, own_flag, other_flag = Ride.rider_id, rider_flag, passenger_flag
    # Read the other participant's flag inside the UPDATE so simultaneous confirmations both count.
    statement = (
        update(Ride)
        .where(Ride.id == ride_id, Ride.status == current, participant == user.id, own_flag.is_(False))
        .values({own_flag: True, Ride.status: case((other_flag.is_(True), next_status), else_=Ride.status)})
    )
    if not _update_ride(db, statement):
        raise DomainError(409, f"You cannot confirm {step} in the current ride state or a second time.")
    return _find_ride(db, ride_id)


def rate_ride(db: Session, user: User, ride_id: int, score: int) -> Ride:
    ride = visible_ride(db, user, ride_id)
    if ride.passenger_id == user.id:
        participant, rating = Ride.passenger_id, Ride.passenger_rating
    else:
        participant, rating = Ride.rider_id, Ride.rider_rating
    statement = (
        update(Ride)
        .where(Ride.id == ride_id, Ride.status == RideStatus.COMPLETED, participant == user.id, rating.is_(None))
        .values({rating: score})
    )
    if not _update_ride(db, statement):
        raise DomainError(409, "You can rate a completed ride once.")
    return _find_ride(db, ride_id)
