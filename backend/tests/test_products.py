from tests.test_auth import test_register_and_verify_email


def test_product_crud_flow(client, db_session):
    test_register_and_verify_email(client, db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List products initially
    list_res = client.get("/api/products")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0

    # Create a product listing
    create_res = client.post(
        "/api/products",
        json={
            "title": "Engineering Physics Textbook",
            "description": "Like new condition, 3rd semester",
            "price": 350.0,
            "category": "Books",
            "negotiable": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    product_data = create_res.json()
    assert product_data["title"] == "Engineering Physics Textbook"
    assert product_data["status"] == "available"

    # Verify item appears in listings
    list_res_2 = client.get("/api/products")
    assert len(list_res_2.json()) == 1

    # Update product status to sold
    product_id = product_data["id"]
    update_res = client.patch(
        f"/api/products/{product_id}/status",
        json={"status": "sold"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "sold"
