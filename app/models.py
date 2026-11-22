from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .domain import Preference, RideStatus, Stop, VerificationStatus, utc_now


def enum_values(enum_class: type[StrEnum]) -> Enum:
    return Enum(
        enum_class,
        values_callable=lambda options: [option.value for option in options],
        native_enum=False,
        create_constraint=True,
    )


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(160))
    is_admin: Mapped[bool] = mapped_column(default=False)
    women_only_eligible: Mapped[bool] = mapped_column(default=False)


class LoginSession(Base):
    __tablename__ = "login_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(index=True)


class Verification(Base):
    __tablename__ = "verifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    mock_reference: Mapped[str] = mapped_column(String(17))
    status: Mapped[VerificationStatus] = mapped_column(enum_values(VerificationStatus))
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class FareQuote(Base):
    __tablename__ = "fare_quotes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pickup: Mapped[Stop] = mapped_column(enum_values(Stop))
    destination: Mapped[Stop] = mapped_column(enum_values(Stop))
    preference: Mapped[Preference] = mapped_column(enum_values(Preference))
    fare_bdt: Mapped[int]
    expires_at: Mapped[datetime]


class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        CheckConstraint("pickup <> destination"),
        CheckConstraint("fare_bdt > 0"),
        CheckConstraint("passenger_id <> rider_id"),
        CheckConstraint("passenger_rating BETWEEN 1 AND 5"),
        CheckConstraint("rider_rating BETWEEN 1 AND 5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[str | None] = mapped_column(ForeignKey("fare_quotes.id"), unique=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rider_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    pickup: Mapped[Stop] = mapped_column(enum_values(Stop))
    destination: Mapped[Stop] = mapped_column(enum_values(Stop))
    preference: Mapped[Preference] = mapped_column(enum_values(Preference))
    fare_bdt: Mapped[int]
    status: Mapped[RideStatus] = mapped_column(enum_values(RideStatus), index=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    passenger_started: Mapped[bool] = mapped_column(default=False)
    rider_started: Mapped[bool] = mapped_column(default=False)
    passenger_completed: Mapped[bool] = mapped_column(default=False)
    rider_completed: Mapped[bool] = mapped_column(default=False)
    passenger_rating: Mapped[int | None]
    rider_rating: Mapped[int | None]

    passenger: Mapped[User] = relationship(foreign_keys=[passenger_id])
    rider: Mapped[User | None] = relationship(foreign_keys=[rider_id])
