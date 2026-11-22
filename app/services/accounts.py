import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..domain import DomainError, VerificationStatus, utc_now
from ..models import LoginSession, User, Verification
from ..schemas import Login, Registration, StudentView, VerificationDecision, VerificationRequest

SESSION_DURATION = timedelta(hours=12)
DUMMY_HASH = "0" * 32 + ":" + "0" * 64


def _derive_key(password: str, salt: bytes) -> str:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**15, r=8, p=3, dklen=32, maxmem=64 * 1024**2
    ).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}:{_derive_key(password, salt)}"


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register(db: Session, data: Registration) -> User:
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        women_only_eligible=data.women_only_eligible,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User.id).where(User.email == data.email)) is not None:
            raise DomainError(409, "That campus email already has an account.") from None
        raise
    return user


def login(db: Session, data: Login, previous_token: str | None) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == data.email))
    salt, expected = (user.password_hash if user else DUMMY_HASH).split(":")
    matches = hmac.compare_digest(_derive_key(data.password, bytes.fromhex(salt)), expected)
    if user is None or not matches:
        raise DomainError(401, "Email or password is incorrect.")

    now = utc_now()
    obsolete = [LoginSession.expires_at <= now]
    if previous_token:
        obsolete.append(LoginSession.token_hash == _token_digest(previous_token))
    db.execute(delete(LoginSession).where(or_(*obsolete)))
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=_token_digest(token), user_id=user.id, expires_at=now + SESSION_DURATION))
    db.commit()
    return user, token


def logout(db: Session, token: str) -> None:
    db.execute(delete(LoginSession).where(LoginSession.token_hash == _token_digest(token)))
    db.commit()


def session_user(db: Session, token: str | None) -> User | None:
    if token is None:
        return None
    return db.scalar(
        select(User)
        .join(LoginSession, LoginSession.user_id == User.id)
        .where(LoginSession.token_hash == _token_digest(token), LoginSession.expires_at > utc_now())
    )


def require_student(user: User) -> None:
    if user.is_admin:
        raise DomainError(403, "This action requires a student account.")


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise DomainError(403, "This action requires an admin account.")


def require_rider(db: Session, user: User) -> None:
    require_student(user)
    verification = db.get(Verification, user.id)
    if verification is None or verification.status != VerificationStatus.APPROVED:
        raise DomainError(403, "Rider approval is required before browsing or accepting rides.")


def profile(user: User, verification: Verification | None = None) -> StudentView:
    roles = ["admin"] if user.is_admin else ["passenger"]
    if verification and verification.status == VerificationStatus.APPROVED:
        roles.append("rider")
    return StudentView(
        id=user.id,
        name=user.name,
        email=user.email,
        roles=roles,
        women_only_eligible=user.women_only_eligible,
        verification_status=verification.status if verification else None,
    )


def verification_for(db: Session, user: User) -> Verification | None:
    require_student(user)
    return db.get(Verification, user.id)


def submit_verification(db: Session, user: User, data: VerificationRequest) -> Verification:
    require_student(user)
    values = {
        "mock_reference": data.mock_reference,
        "status": VerificationStatus.PENDING,
        "reviewed_by_id": None,
    }
    # The same account may submit again after a rejection.
    request = insert(Verification).values(user_id=user.id, **values)
    request = request.on_conflict_do_update(
        index_elements=[Verification.user_id],
        set_=values,
        where=Verification.status == VerificationStatus.REJECTED,
    )
    if db.execute(request).rowcount != 1:
        raise DomainError(409, "This account already has a pending or approved rider request.")
    db.commit()
    return db.get(Verification, user.id)


def review_verification(
    db: Session, admin: User, user_id: int, data: VerificationDecision
) -> Verification:
    require_admin(admin)
    result = db.execute(
        update(Verification)
        .where(Verification.user_id == user_id, Verification.status == VerificationStatus.PENDING)
        .values(status=data.status, reviewed_by_id=admin.id)
    )
    if result.rowcount != 1:
        if db.get(Verification, user_id) is None:
            raise DomainError(404, "Rider verification request not found.")
        raise DomainError(409, "This request has already been reviewed.")
    db.commit()
    return db.get(Verification, user_id)
