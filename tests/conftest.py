import os
import pytest # type: ignore
from moto import mock_aws # type: ignore

os.environ["SECRET_KEY"] = "test-secret"
os.environ["USERS_TABLE"] = "users"
os.environ["MESSAGES_TABLE"] = "messages"
os.environ["STATS_TABLE"] = "stats"
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

from database import dynamo
from database.local import create_tables

@pytest.fixture(autouse=True)
def fake_dynamodb():
    with mock_aws():
        dynamo.connect_to_dynamodb.cache_clear()
        create_tables()
        yield

@pytest.fixture
def client():
    from fastapi.testclient import TestClient # type: ignore
    from app import app
    return TestClient(app, base_url="https://testserver")
