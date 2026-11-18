import os

import mongomock
import pytest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("MONGODB_URL", "mongodb://unused")


@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    client = mongomock.MongoClient()
    monkeypatch.setattr("database.connection.connect_to_mongo", lambda: client)
    yield client


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app import app

    return TestClient(app, base_url="https://testserver")  # cookies are Secure
