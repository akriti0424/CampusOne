from tests.test_auth import test_register_and_verify_email


def test_chat_messages_rest_flow(client, db_session):
    test_register_and_verify_email(client, db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch initial chat room history
    history_res = client.get("/api/chat/general", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) == 0

    # Post a new message
    post_res = client.post(
        "/api/chat",
        json={"room_name": "general", "message": "Hello MANIT!"},
        headers=headers,
    )
    assert post_res.status_code == 200
    msg = post_res.json()
    assert msg["message"] == "Hello MANIT!"
    assert msg["author_id"] is not None

    # Fetch updated history
    history_res_2 = client.get("/api/chat/general", headers=headers)
    assert history_res_2.status_code == 200
    assert len(history_res_2.json()) == 1
    assert history_res_2.json()[0]["author_id"] == msg["author_id"]
