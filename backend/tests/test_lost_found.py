from tests.test_auth import test_register_and_verify_email


def test_lost_found_reporting_and_matching(client, db_session):
    test_register_and_verify_email(client, db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Report a lost item
    lost_res = client.post(
        "/api/lost-found/items",
        json={
            "kind": "lost",
            "title": "Blue Dell Laptop Bag",
            "description": "Contains CS lab notebook and charger",
            "location": "Central Library",
        },
        headers=headers,
    )
    assert lost_res.status_code == 200
    lost_item = lost_res.json()
    assert lost_item["kind"] == "lost"
    assert lost_item["status"] == "open"

    # Fetch my reported items
    my_items = client.get("/api/lost-found/items", headers=headers)
    assert my_items.status_code == 200
    assert len(my_items.json()) == 1

    # Request verification code for desk handover
    verify_req = client.post(
        f"/api/lost-found/items/{lost_item['id']}/verification-request",
        headers=headers,
    )
    assert verify_req.status_code == 200
    assert "verification_code" in verify_req.json()
    assert verify_req.json()["status"] == "matched"
