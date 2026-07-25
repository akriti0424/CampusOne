from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import smtplib
from email.message import EmailMessage

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
    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is not configured. Set SMTP settings before registration.",
        )

    message = EmailMessage()
    message["Subject"] = "Your CampusOne verification code"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        f"Your CampusOne verification code is {otp}. "
        f"It expires in {settings.email_otp_expire_minutes} minutes."
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not send verification email") from error


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
