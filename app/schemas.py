import re
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

from .domain import Preference, RideStatus, Stop, VerificationStatus

CAMPUS_EMAIL = re.compile(r"[a-z0-9_+%-]+(?:\.[a-z0-9_+%-]+)*@campus\.example", re.ASCII)


def campus_email(value: str) -> str:
    value = value.strip().lower()
    if not CAMPUS_EMAIL.fullmatch(value) or len(value.split("@")[0]) > 64:
        raise ValueError("Use a fictional @campus.example email address.")
    return value


CampusEmail = Annotated[str, StringConstraints(max_length=100), AfterValidator(campus_email)]
UTCDateTime = Annotated[datetime, AfterValidator(lambda value: value.replace(tzinfo=UTC))]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Registration(Input):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]
    email: CampusEmail
    password: str = Field(min_length=10, max_length=128)
    women_only_eligible: StrictBool = False

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("Use at least one letter and one digit.")
        return value


class Login(Input):
    email: CampusEmail
    password: str = Field(min_length=1, max_length=128)


class StudentView(BaseModel):
    id: int
    name: str
    email: str
    roles: list[Literal["passenger", "rider", "admin"]]
    women_only_eligible: bool
    verification_status: VerificationStatus | None


class VerificationRequest(Input):
    mock_reference: str = Field(pattern=r"^MOCK-[A-Z0-9]{3,12}$", max_length=17)


class VerificationDecision(Input):
    status: Literal[VerificationStatus.APPROVED, VerificationStatus.REJECTED]


class VerificationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    mock_reference: str
    status: VerificationStatus


class RideRoute(Input):
    pickup: Stop
    destination: Stop
    preference: Preference

    @model_validator(mode="after")
    def different_stops(self) -> "RideRoute":
        if self.pickup == self.destination:
            raise ValueError("Choose a destination different from your pickup.")
        return self


class QuoteView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Quote ID to use when confirming a booking.")
    pickup: Stop
    destination: Stop
    preference: Preference
    fare_bdt: int
    expires_at: UTCDateTime


class Booking(Input):
    quote_id: str = Field(pattern=r"^[a-f0-9]{32}$")


class RatingInput(Input):
    score: int = Field(strict=True, ge=1, le=5)


class RideSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pickup: Stop
    destination: Stop
    preference: Preference
    fare_bdt: int
    status: RideStatus
    created_at: UTCDateTime


class RideDetail(RideSummary):
    passenger_name: str
    rider_name: str | None
    passenger_started: bool
    rider_started: bool
    passenger_completed: bool
    rider_completed: bool
    my_rating: int | None
    received_rating: int | None = Field(description="Visible to a participant after both ratings exist.")


class PendingVerification(VerificationView):
    name: str
    email: str


class AdminStats(BaseModel):
    students: int
    approved_riders: int
    pending_verifications: int
    rides_by_status: dict[RideStatus, int]


class AdminDashboard(BaseModel):
    stats: AdminStats
    accounts: list[StudentView]
    pending_verifications: list[PendingVerification]
    rides: list[RideSummary]
