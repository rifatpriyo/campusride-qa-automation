from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .db import open_database
from .domain import Preference, RideStatus, Stop, VerificationStatus
from .models import Base, Ride, User, Verification
from .services.accounts import hash_password
from .services.rides import fare_for

DEMO_PASSWORD = "CampusDemo2026!"


@dataclass(frozen=True)
class DemoAccount:
    name: str
    email: str
    eligible: bool = False
    verification: VerificationStatus | None = None


DEMO_ACCOUNTS = {
    "mira": DemoAccount("Mira Rahman", "mira@campus.example", eligible=True),
    "anika": DemoAccount("Anika Karim", "anika@campus.example", True, VerificationStatus.APPROVED),
    "tariq": DemoAccount("Tariq Hasan", "tariq@campus.example", False, VerificationStatus.APPROVED),
    "sami": DemoAccount("Sami Chowdhury", "sami@campus.example", False, VerificationStatus.PENDING),
    "admin": DemoAccount("Nadia Ahmed", "admin@campus.example"),
}


def seed_demo(db: Session) -> bool:
    existing = dict(db.execute(
        select(User.email, User.is_admin).where(User.email.in_([account.email for account in DEMO_ACCOUNTS.values()]))
    ).all())
    # A successful seed writes the admin and all fixtures in one transaction.
    if existing.get(DEMO_ACCOUNTS["admin"].email):
        return False
    if existing:
        raise ValueError("A demo email is already in use. Choose a fresh database to load the demo fixtures.")

    users = {
        key: User(
            name=account.name,
            email=account.email,
            password_hash=hash_password(DEMO_PASSWORD),
            women_only_eligible=account.eligible,
            is_admin=key == "admin",
        )
        for key, account in DEMO_ACCOUNTS.items()
    }
    db.add_all(users.values())
    db.flush()

    for key, account in DEMO_ACCOUNTS.items():
        if account.verification:
            db.add(Verification(
                user_id=users[key].id,
                mock_reference=f"MOCK-{key.upper()}26",
                status=account.verification,
                reviewed_by_id=users["admin"].id if account.verification == VerificationStatus.APPROVED else None,
            ))

    def fixture_ride(
        passenger: str,
        pickup: Stop,
        destination: Stop,
        status: RideStatus,
        rider: str | None = None,
        preference: Preference = Preference.REGULAR,
    ) -> Ride:
        started = status in {RideStatus.IN_PROGRESS, RideStatus.COMPLETED}
        completed = status == RideStatus.COMPLETED
        return Ride(
            passenger_id=users[passenger].id,
            rider_id=users[rider].id if rider else None,
            pickup=pickup,
            destination=destination,
            status=status,
            preference=preference,
            fare_bdt=fare_for(pickup, destination),
            passenger_started=started,
            rider_started=started,
            passenger_completed=completed,
            rider_completed=completed,
            passenger_rating=5 if completed else None,
            rider_rating=4 if completed else None,
        )

    samples = [
        fixture_ride("mira", Stop.ENGINEERING_HALL, Stop.NORTH_GATE, RideStatus.COMPLETED, "anika", Preference.WOMEN_ONLY),
        fixture_ride("sami", Stop.MAIN_LIBRARY, Stop.NORTH_GATE, RideStatus.CANCELLED),
        fixture_ride("sami", Stop.ENGINEERING_HALL, Stop.RESIDENCE_QUAD, RideStatus.IN_PROGRESS, "tariq"),
        fixture_ride("mira", Stop.STUDENT_CENTER, Stop.ENGINEERING_HALL, RideStatus.ACCEPTED, "tariq"),
        fixture_ride("anika", Stop.RESIDENCE_QUAD, Stop.STUDENT_CENTER, RideStatus.REQUESTED),
        fixture_ride("mira", Stop.MAIN_LIBRARY, Stop.RESIDENCE_QUAD, RideStatus.REQUESTED, preference=Preference.WOMEN_ONLY),
        fixture_ride("mira", Stop.NORTH_GATE, Stop.ENGINEERING_HALL, RideStatus.REQUESTED),
    ]
    for index, ride in enumerate(samples):
        ride.created_at = datetime(2026, 1, 12, 3) + timedelta(hours=index)

    db.add_all(samples)
    db.commit()
    return True


def main() -> None:
    path = Settings.from_env().database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = open_database(path)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            created = seed_demo(db)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    finally:
        engine.dispose()

    print(f"{'Demo data loaded' if created else 'Demo data already exists'} in {path}")


if __name__ == "__main__":
    main()
