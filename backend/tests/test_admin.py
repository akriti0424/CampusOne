from tests.test_auth import test_register_and_verify_email
from app.modules.auth.model import User
from app.core.security import hash_password


def _create_admin_user(db_session) -> User:
    admin = User(
        full_name="Campus Admin",
        scholar_id="MANIT-ADMIN-99",
        branch="Admin",
        email="admin_test@stu.manit.ac.in",
        password_hash=hash_password("Admin1234!"),
        role="admin",
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def test_admin_list_and_delete_user(client, db_session):
    # Setup student user
    test_register_and_verify_email(client, db_session)

    # Setup admin user
    _create_admin_user(db_session)

    # Login as admin
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin_test@stu.manit.ac.in", "password": "Admin1234!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List users
    users_res = client.get("/api/admin/users", headers=headers)
    assert users_res.status_code == 200
    users = users_res.json()
    assert len(users) >= 2

    # Find student ID to delete
    student_user = next(u for u in users if u["email"] == "test@stu.manit.ac.in")

    # Delete student user
    del_res = client.delete(f"/api/admin/users/{student_user['id']}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "User deleted successfully"

    # Verify user list length reduced
    users_res_2 = client.get("/api/admin/users", headers=headers)
    assert len(users_res_2.json()) == len(users) - 1


def test_non_admin_cannot_access_admin_routes(client, db_session):
    test_register_and_verify_email(client, db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users_res = client.get("/api/admin/users", headers=headers)
    assert users_res.status_code == 403


def test_admin_cannot_delete_self(client, db_session):
    admin = _create_admin_user(db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin_test@stu.manit.ac.in", "password": "Admin1234!"},
    )
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    del_self_res = client.delete(f"/api/admin/users/{admin.id}", headers=headers)
    assert del_self_res.status_code == 400
    assert "own account" in del_self_res.json()["detail"]
