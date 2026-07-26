from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import httpx

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.model import PendingRegistration, User
from app.modules.auth.schema import UserCreate, UserLogin


def _validate_campus_email(email: str) -> None:
    if not email.endswith(settings.campus_email_domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {settings.campus_email_domain} emails are allowed",
        )


def register_pending_user(db: Session, payload: UserCreate) -> PendingRegistration:
    _validate_campus_email(payload.email)

    existing_user = db.query(User).filter((User.email == payload.email) | (User.scholar_id == payload.scholar_id)).first()
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        # Clean up records created by the former registration flow, which saved unverified users.
        db.delete(existing_user)
        db.flush()

    existing_pending = db.query(PendingRegistration).filter(
        (PendingRegistration.email == payload.email) | (PendingRegistration.scholar_id == payload.scholar_id)
    ).first()
    if existing_pending:
        db.delete(existing_pending)
        db.flush()

    otp = _generate_otp()
    pending = PendingRegistration(
        full_name=payload.full_name.strip(),
        scholar_id=payload.scholar_id.strip().upper(),
        branch=payload.branch.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        email_otp_hash=_hash_otp(otp),
        email_otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.email_otp_expire_minutes),
    )
    db.add(pending)
    send_verification_email(pending.email, otp)
    db.commit()
    db.refresh(pending)
    return pending


def _generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def send_verification_email(email: str, otp: str) -> None:
    api_key = settings.BREVO_API_KEY or settings.brevo_api_key
    sender_email = settings.BREVO_SENDER_EMAIL or settings.brevo_sender_email

    # Always log OTP in development mode for easy local debugging
    if settings.environment.lower() == "development":
        print(f"\n[DEV MODE OTP LOG] 🔑 Verification code for {email}: {otp}\n")

    if not api_key or not sender_email:
        if settings.environment.lower() == "development":
            print("API Key is not set. OTP logged above.")
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Brevo email delivery is not configured. Set BREVO_API_KEY and BREVO_SENDER_EMAIL.",
        )

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    payload = {
        "sender": {"name": "CampusOne", "email": sender_email},
        "to": [{"email": email}],
        "subject": "Your CampusOne verification code",
        "htmlContent": f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#070d19; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#070d19; padding:40px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width:500px; background-color:#0d172a; border:1px solid rgba(255,255,255,0.1); border-radius:20px; box-shadow:0 20px 40px rgba(0,0,0,0.5); overflow:hidden;" border="0" cellspacing="0" cellpadding="0">
          <tr>
            <td style="padding:32px 32px 20px 32px; text-align:center; border-bottom:1px solid rgba(255,255,255,0.08);">
              <div style="display:inline-block; background:linear-gradient(135deg, #a3f7db, #4dd0a8); color:#031b15; font-size:24px; font-weight:800; width:48px; height:48px; line-height:48px; border-radius:14px; text-align:center; margin-bottom:10px;">C</div>
              <h1 style="margin:0; color:#f1f5f9; font-size:24px; font-weight:700; letter-spacing:-0.5px;">CampusOne</h1>
              <p style="margin:4px 0 0 0; color:#94a3b8; font-size:12px; text-transform:uppercase; letter-spacing:1.5px; font-weight:600;">MANIT Campus Platform</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px; text-align:center;">
              <h2 style="margin:0 0 12px 0; color:#ffffff; font-size:20px; font-weight:600;">Verify Your Email Address</h2>
              <p style="margin:0 0 24px 0; color:#cbd5e1; font-size:14px; line-height:1.6;">
                Welcome to <b>CampusOne</b>! Please enter the 6-digit verification code below to complete your registration.
              </p>
              <div style="background-color:#040913; border:1px solid rgba(77,208,168,0.3); border-radius:14px; padding:18px 16px; margin:20px 0; display:inline-block; width:82%;">
                <span style="font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:34px; font-weight:800; letter-spacing:10px; color:#4dd0a8;">{otp}</span>
              </div>
              <p style="margin:14px 0 0 0; color:#f5b84a; font-size:13px; font-weight:500;">
                ⏰ This code will expire in <b>{settings.email_otp_expire_minutes} minutes</b>.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 28px 32px; text-align:center; border-top:1px solid rgba(255,255,255,0.08); background-color:rgba(0,0,0,0.2);">
              <p style="margin:0 0 6px 0; color:#64748b; font-size:12px;">
                If you did not request this code, please ignore this email.
              </p>
              <p style="margin:0; color:#475569; font-size:12px; font-weight:600;">
                © CampusOne • Exclusive to @stu.manit.ac.in
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>""",
    }

    try:
        response = httpx.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=10.0)
        if response.status_code not in (200, 201, 202):
            print(f"Brevo API Error ({response.status_code}): {response.text}")
            if settings.environment.lower() == "development":
                return
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send verification email",
            )
    except Exception as error:
        print(f"Brevo HTTP Error: {error}")
        if settings.environment.lower() == "development":
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not send verification email",
        ) from error


def issue_verification_otp(db: Session, pending: PendingRegistration) -> None:
    otp = _generate_otp()
    pending.email_otp_hash = _hash_otp(otp)
    pending.email_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.email_otp_expire_minutes)
    send_verification_email(pending.email, otp)
    db.commit()


def verify_email_otp(db: Session, email: str, otp: str) -> User:
    pending = db.query(PendingRegistration).filter(PendingRegistration.email == email.lower()).first()
    if not pending:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending registration found")
    if pending.email_otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
    if _hash_otp(otp) != pending.email_otp_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    user = User(
        full_name=pending.full_name,
        scholar_id=pending.scholar_id,
        branch=pending.branch,
        email=pending.email,
        password_hash=pending.password_hash,
        is_verified=True,
    )
    db.add(user)
    db.delete(pending)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: UserLogin) -> tuple[User, str]:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(subject=str(user.id))
    return user, token


def public_user_name(user: User) -> str:
    return user.full_name.split()[0] if user.full_name else "Student"
