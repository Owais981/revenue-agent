import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    db_url = os.environ["DATABASE_URL"]
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "tester@example.com", "password": "TestPass123!"},
    )
    resp = client.post("/api/auth/login", json={"email": "tester@example.com", "password": "TestPass123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
