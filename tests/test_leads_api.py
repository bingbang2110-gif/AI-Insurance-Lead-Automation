
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.database.database import Base
from app.api import leads as leads_api


@pytest.fixture
def client(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    monkeypatch.setattr(
        leads_api,
        "SessionLocal",
        TestingSessionLocal,
    )

    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_create_lead(client):
    response = client.post(
        "/leads/",
        json={
            "name": "Ali Test",
            "email": "ali@example.com",
            "phone": "+989121234567",
            "coverage_type": "auto",
            "urgency": "high",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Ali Test"
    assert data["email"] == "ali@example.com"
    assert data["lead_score"] == 65
    assert data["priority"] == "medium"


def test_get_leads(client):
    client.post(
        "/leads/",
        json={
            "name": "Sara Test",
            "email": "sara@example.com",
            "phone": "+989121234568",
            "coverage_type": "health",
        },
    )

    response = client.get("/leads/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Sara Test"


def test_get_nonexistent_lead(client):
    response = client.get("/leads/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Lead not found"
def test_create_lead_with_invalid_email(client):
    response = client.post(
        "/leads/",
        json={
            "name": "Ali Test",
            "email": "invalid-email",
            "phone": "+989121234567",
            "coverage_type": "auto",
        },
    )
    assert response.status_code == 422


def test_create_lead_with_empty_name(client):
    response = client.post(
        "/leads/",
        json={
            "name": "   ",
            "email": "ali@example.com",
            "phone": "+989121234567",
            "coverage_type": "auto",
        },
    )
    assert response.status_code == 422