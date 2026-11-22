from datetime import UTC, datetime
from enum import StrEnum


class Stop(StrEnum):
    NORTH_GATE = "north_gate"
    MAIN_LIBRARY = "main_library"
    ENGINEERING_HALL = "engineering_hall"
    STUDENT_CENTER = "student_center"
    RESIDENCE_QUAD = "residence_quad"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").title()


class Preference(StrEnum):
    REGULAR = "regular"
    WOMEN_ONLY = "women_only"


class RideStatus(StrEnum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DomainError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def utc_now() -> datetime:
    # SQLite stores naive datetimes. All dates written by the app are UTC.
    return datetime.now(UTC).replace(tzinfo=None)
