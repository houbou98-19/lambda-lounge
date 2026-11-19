import boto3 # type: ignore
CREDS = {"username": "Mark", "password": "pw12345"}


def test_login_page_served(client):
    assert client.get("/login").status_code == 200


def test_messages_require_auth(client):
    assert client.get("/messages").status_code == 401
    assert client.post("/messages", json={"content": "hi"}).status_code == 401


def test_register_login_and_chat_flow(client):
    assert client.post("/register", data=CREDS).status_code == 200
    assert client.post("/register", data=CREDS).status_code == 400  # duplicate

    assert client.post("/token", data={**CREDS, "password": "wrong"}).status_code == 401
    assert client.post("/token", data=CREDS).status_code == 200

    assert client.post("/messages", json={"content": "hello"}).status_code == 200
    msgs = client.get("/messages").json()
    assert [(m["username"], m["messagecontent"]) for m in msgs] == [("Mark", "hello")]
    assert msgs[0]["timestamp"].isdigit()


def test_logout_clears_access(client):
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    client.post("/logout")
    assert client.get("/messages").status_code == 401


def test_messages_are_ordered_oldest_to_newest(client):
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    for text in ("one", "two", "three"):
        client.post("/messages", json={"content": text})
    assert [m["messagecontent"] for m in client.get("/messages").json()] == ["one", "two", "three"]


def test_messages_returns_only_latest_page(client):
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    for i in range(105):
        client.post("/messages", json={"content": str(i)})
    msgs = client.get("/messages").json()
    assert len(msgs) == 100
    assert msgs[-1]["messagecontent"] == "104"


def test_stats_require_auth(client):
    assert client.get("/stats").status_code == 401


def test_stats_returns_top_users(client, fake_dynamodb):
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    stats = boto3.resource("dynamodb").Table("stats")
    stats.put_item(Item={"username": "alice", "message_count": 3})
    stats.put_item(Item={"username": "bob", "message_count": 7})
    assert client.get("/stats").json() == [{"username": "bob", "messages": 7}, {"username": "alice", "messages": 3}]
