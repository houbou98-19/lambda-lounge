# Runs the app locally with a fake in-memory DynamoDB: python dev.py
import os

os.environ["SECRET_KEY"] = "local-secret"
os.environ["USERS_TABLE"] = "users"
os.environ["MESSAGES_TABLE"] = "messages"
os.environ["STATS_TABLE"] = "stats"
os.environ["CONNECTIONS_TABLE"] = "connections"
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_ACCESS_KEY_ID"] = "local"
os.environ["AWS_SECRET_ACCESS_KEY"] = "local"

import uvicorn # type: ignore
from moto import mock_aws # type: ignore
from database.local import create_tables

if __name__ == "__main__":
    with mock_aws():
        create_tables()
        from app import app
        uvicorn.run(app, host="127.0.0.1", port=8000)
