import json
import boto3 # type: ignore
from datetime import timedelta
from unittest.mock import MagicMock, patch
from auth.utils import create_access_token
from workers import broadcaster, ws_connection

CREDS = {"username": "alice", "password": "pw12345"}

def ws_event(route, connection_id="abc", ticket=None):
    event = {"requestContext": {"routeKey": route, "connectionId": connection_id}}
    if ticket:
        event["queryStringParameters"] = {"ticket": ticket}
    return event

def ticket_for(username, expires=timedelta(seconds=60)):
    return create_access_token(data={"sub": username, "scope": "ws"}, expires_delta=expires)

def test_connect_with_a_good_ticket_saves_the_connection():
    result = ws_connection.lambda_handler(ws_event("$connect", ticket=ticket_for("alice")), None)
    assert result == {"statusCode": 200}
    item = boto3.resource("dynamodb").Table("connections").get_item(Key={"connectionId": "abc"})["Item"]
    assert item["username"] == "alice"

def test_connect_is_refused_without_a_good_ticket():
    login_token = create_access_token(data={"sub": "alice"})  # normal token, no ws scope
    for event in (ws_event("$connect"), ws_event("$connect", ticket="rubbish"), ws_event("$connect", ticket=login_token),
                  ws_event("$connect", ticket=ticket_for("alice", timedelta(seconds=-1)))):
        assert ws_connection.lambda_handler(event, None) == {"statusCode": 401}
    assert boto3.resource("dynamodb").Table("connections").scan()["Items"] == []

def test_disconnect_removes_the_connection():
    ws_connection.lambda_handler(ws_event("$connect", ticket=ticket_for("alice")), None)
    ws_connection.lambda_handler(ws_event("$disconnect"), None)
    assert boto3.resource("dynamodb").Table("connections").scan()["Items"] == []

def test_broadcaster_sends_to_everyone_and_forgets_who_hung_up():
    table = boto3.resource("dynamodb").Table("connections")
    for connection_id in ("one", "two", "three"):
        table.put_item(Item={"connectionId": connection_id, "username": "x"})

    class Gone(Exception):
        pass

    client = MagicMock()
    client.exceptions.GoneException = Gone
    client.post_to_connection.side_effect = lambda ConnectionId, Data: (_ for _ in ()).throw(Gone()) if ConnectionId == "two" else None
    event = {"detail": {"username": "bob", "messagecontent": "hello", "timestamp": "123"}}
    with patch("workers.broadcaster.boto3.client", return_value=client):
        broadcaster.lambda_handler(event, None)

    assert client.post_to_connection.call_count == 3
    sent = json.loads(client.post_to_connection.call_args.kwargs["Data"])
    assert sent == {"username": "bob", "messagecontent": "hello", "timestamp": "123"}
    left = {i["connectionId"] for i in table.scan()["Items"]}
    assert left == {"one", "three"}

def test_ws_token_is_not_available_without_a_websocket_url(client):
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    assert client.get("/ws-token").status_code == 404

def test_ws_token_needs_login(client, monkeypatch):
    monkeypatch.setenv("WEBSOCKET_URL", "wss://example.test/Prod")
    assert client.get("/ws-token").status_code == 401

def test_ws_ticket_works_for_websocket_but_not_as_login(client, monkeypatch):
    monkeypatch.setenv("WEBSOCKET_URL", "wss://example.test/Prod")
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    body = client.get("/ws-token").json()
    assert body["url"] == "wss://example.test/Prod"

    result = ws_connection.lambda_handler(ws_event("$connect", ticket=body["ticket"]), None)
    assert result == {"statusCode": 200}

    client.cookies.set("access_token", body["ticket"])  # a ticket used as a login cookie
    assert client.get("/messages").status_code == 401
