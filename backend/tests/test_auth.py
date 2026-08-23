from app.modules.auth.model import PendingRegistration, User
from app.modules.auth.service import _hash_otp


def test_register_invalid_email_domain(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "John Doe",
            "scholar_id": "22CS1001",
            "branch": "CSE",
            "email": "john@gmail.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "stu.manit.ac.in" in response.json()["detail"]


def test_register_and_verify_email(client, db_session):
    reg_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Student",
            "scholar_id": "22CS1002",
            "branch": "Computer Science",
            "email": "test@stu.manit.ac.in",
            "password": "password123",
        },
    )
    assert reg_response.status_code == 201

    pending = db_session.query(PendingRegistration).filter_by(email="test@stu.manit.ac.in").first()
    assert pending is not None

    # Manually overwrite hash to known OTP "123456" for verification test
    pending.email_otp_hash = _hash_otp("123456")
    db_session.commit()

    verify_response = client.post(
        "/api/auth/verify-email",
        json={"email": "test@stu.manit.ac.in", "otp": "123456"},
    )
    assert verify_response.status_code == 200
    data = verify_response.json()
    assert "token" in data
    assert data["user"]["email"] == "test@stu.manit.ac.in"
    assert data["user"]["is_verified"] is True


def test_login_success_and_failure(client, db_session):
    # Setup verified user
    test_register_and_verify_email(client, db_session)

    # Failed login
    fail_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "wrongpassword"},
    )
    assert fail_res.status_code == 401

    # Successful login
    success_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    assert success_res.status_code == 200
    assert "token" in success_res.json()


def test_get_current_user_me(client, db_session):
    test_register_and_verify_email(client, db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    token = login_res.json()["token"]["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "test@stu.manit.ac.in"


def test_change_password(client, db_session):
    test_register_and_verify_email(client, db_session)
    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "password123"},
    )
    token = login_res.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Wrong current password
    wrong_pwd_res = client.post(
        "/api/auth/change-password",
        json={"current_password": "incorrectpassword", "new_password": "newpassword123"},
        headers=headers,
    )
    assert wrong_pwd_res.status_code == 400

    # Successful password change
    change_res = client.post(
        "/api/auth/change-password",
        json={"current_password": "password123", "new_password": "newpassword123"},
        headers=headers,
    )
    assert change_res.status_code == 200

    # Verify login with new password
    new_login = client.post(
        "/api/auth/login",
        json={"email": "test@stu.manit.ac.in", "password": "newpassword123"},
    )
    assert new_login.status_code == 200

