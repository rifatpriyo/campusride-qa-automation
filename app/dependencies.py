from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session

from .domain import DomainError
from .models import User
from .services.accounts import session_user

SESSION_COOKIE = "campusride_session"


def get_db(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as db:
        yield db


Db = Annotated[Session, Depends(get_db)]
SessionToken = Annotated[
    str | None,
    Security(APIKeyCookie(
        name=SESSION_COOKIE,
        scheme_name="CampusRideSession",
        description="Sign in from this browser to set the session cookie.",
        auto_error=False,
    )),
]


def get_viewer(request: Request, db: Db, token: SessionToken) -> User | None:
    viewer = session_user(db, token)
    request.state.viewer = viewer
    return viewer


Viewer = Annotated[User | None, Depends(get_viewer)]


def require_user(viewer: Viewer) -> User:
    if viewer is None:
        raise DomainError(401, "Sign in to continue.")
    return viewer


CurrentUser = Annotated[User, Depends(require_user)]


def require_same_origin_for_writes(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origin = request.headers.get("origin")
    expected = f"{request.url.scheme}://{request.url.netloc}"
    if (origin is not None and origin != expected) or request.headers.get("sec-fetch-site") in {
        "cross-site", "same-site"
    }:
        raise DomainError(403, "Submit this action from CampusRide's own page.")
