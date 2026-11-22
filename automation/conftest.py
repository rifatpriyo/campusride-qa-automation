import shutil
import socket
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event, Thread

import pytest
import uvicorn
from playwright.sync_api import Page, expect
from pytest_playwright.pytest_playwright import CreateContextCallback
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import open_database
from app.demo import DEMO_ACCOUNTS, DEMO_PASSWORD, seed_demo
from app.main import create_app
from app.models import Base
from automation.pages.login import LoginPage


class _LocalServer(uvicorn.Server):
    def __init__(self, config: uvicorn.Config):
        super().__init__(config)
        self.ready = Event()

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        await super().startup(sockets=sockets)
        self.ready.set()


@pytest.fixture(scope="session")
def demo_database(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("ui-demo") / "seed.db"
    engine = open_database(path)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            assert seed_demo(db)
    finally:
        engine.dispose()
    return path


@pytest.fixture
def local_app(tmp_path: Path, demo_database: Path) -> Iterator[str]:
    database = tmp_path / "campusride.db"
    shutil.copyfile(demo_database, database)
    app = create_app(Settings(database_path=database, demo_bug_mode=False, secure_cookie=False))
    server = _LocalServer(uvicorn.Config(
        app, workers=1, log_level="warning", proxy_headers=False, timeout_graceful_shutdown=5,
    ))

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

        def run() -> None:
            try:
                server.run(sockets=[listener])
            finally:
                server.ready.set()

        thread = Thread(target=run, name="campusride-ui-server", daemon=True)
        thread.start()
        try:
            if not server.ready.wait(timeout=15) or not server.started:
                pytest.fail("CampusRide did not start on loopback. Check the captured server output.")
            yield f"http://127.0.0.1:{port}"
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            if thread.is_alive():
                pytest.fail("The CampusRide test server did not shut down.")


@pytest.fixture
def browser_context_args(browser_context_args: dict, local_app: str) -> dict:
    return {**browser_context_args, "base_url": local_app}


@pytest.fixture
def open_page(new_context: CreateContextCallback) -> Callable[[], Page]:
    def new_page() -> Page:
        context = new_context()
        context.set_default_timeout(6_000)
        context.set_default_navigation_timeout(12_000)
        return context.new_page()

    return new_page


@pytest.fixture
def sign_in(open_page: Callable[[], Page]) -> Callable[[str], Page]:
    dashboards = {"mira": "passenger", "sami": "passenger", "anika": "rider", "tariq": "rider", "admin": "admin"}

    def signed_in_page(account: str) -> Page:
        page = open_page()
        login = LoginPage(page)
        login.open()
        login.sign_in(DEMO_ACCOUNTS[account].email, DEMO_PASSWORD)
        expect(page).to_have_url(f"/{dashboards[account]}")
        return page

    return signed_in_page


def pytest_configure() -> None:
    expect.set_options(timeout=6_000)


@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report) -> None:
    report.title = "CampusRide QA Lab | Chromium UI Tests"
