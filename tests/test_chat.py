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
    assert msgs == [{"username": "Mark", "messagecontent": "hello"}]


def test_logout_clears_access(client):
    client.post("/register", data=CREDS)
    client.post("/token", data=CREDS)
    client.post("/logout")
    assert client.get("/messages").status_code == 401
