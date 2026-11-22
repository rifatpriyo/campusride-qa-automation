import shutil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import open_database
from app.demo import DEMO_ACCOUNTS, DEMO_PASSWORD, seed_demo
from app.main import create_app
from app.models import Base


@pytest.fixture(scope="session")
def demo_database(tmp_path_factory):
    path = tmp_path_factory.mktemp("demo") / "seed.db"
    engine = open_database(path)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            assert seed_demo(db)
    finally:
        engine.dispose()
    return path


@pytest.fixture
def site(tmp_path, demo_database):
    path = tmp_path / "campusride.db"
    shutil.copyfile(demo_database, path)
    app = create_app(Settings(database_path=path))
    with TestClient(app) as client:
        yield app, client


@pytest.fixture
def client(site):
    return site[1]


@pytest.fixture
def sign_in(site):
    app, _ = site
    clients = []

    def signed_in_client(account):
        client = TestClient(app)
        clients.append(client)
        response = client.post("/api/auth/login", json={
            "email": DEMO_ACCOUNTS[account].email,
            "password": DEMO_PASSWORD,
        })
        assert response.status_code == 200, response.text
        return client

    yield signed_in_client
    for client in clients:
        client.close()
