from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain import RideStatus, VerificationStatus
from ..models import Ride, User, Verification
from ..schemas import AdminDashboard, AdminStats, PendingVerification, RideSummary
from .accounts import profile, require_admin


def dashboard(db: Session, admin: User) -> AdminDashboard:
    require_admin(admin)
    accounts = []
    pending = []
    for user, verification in db.execute(
        select(User, Verification).outerjoin(Verification, User.id == Verification.user_id).order_by(User.id)
    ):
        accounts.append(profile(user, verification))
        if verification and verification.status == VerificationStatus.PENDING:
            pending.append(PendingVerification(
                user_id=user.id,
                name=user.name,
                email=user.email,
                mock_reference=verification.mock_reference,
                status=verification.status,
            ))
    rides = [RideSummary.model_validate(ride) for ride in db.scalars(select(Ride).order_by(Ride.id.desc()))]
    counts = Counter(ride.status for ride in rides)
    return AdminDashboard(
        stats=AdminStats(
            students=sum("passenger" in account.roles for account in accounts),
            approved_riders=sum("rider" in account.roles for account in accounts),
            pending_verifications=len(pending),
            rides_by_status={status: counts[status] for status in RideStatus},
        ),
        accounts=accounts,
        pending_verifications=pending,
        rides=rides,
    )
