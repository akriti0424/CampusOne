from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.model import PendingRegistration, User
from app.modules.auth.schema import (
    AuthResponse, EmailVerificationSubmit, RegistrationResponse, ResendVerificationRequest,
    Token, UserCreate, UserLogin, UserRead,
)
from app.modules.auth.service import authenticate_user, issue_verification_otp, register_pending_user, verify_email_otp


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegistrationResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    pending = register_pending_user(db, payload)
    return RegistrationResponse(message="Verification code sent to your campus email", email=pending.email)


@router.post("/verify-email", response_model=AuthResponse)
def verify_email(payload: EmailVerificationSubmit, db: Session = Depends(get_db)):
    user = verify_email_otp(db, payload.email, payload.otp)
    token = Token(access_token=create_access_token(subject=str(user.id)))
    return AuthResponse(token=token, user=UserRead.model_validate(user))


@router.post("/resend-verification", response_model=RegistrationResponse)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    pending = db.query(PendingRegistration).filter(PendingRegistration.email == payload.email.lower()).first()
    if not pending:
        raise HTTPException(status_code=404, detail="No pending registration found")
    issue_verification_otp(db, pending)
    return RegistrationResponse(message="A new verification code was sent", email=pending.email)


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user, access_token = authenticate_user(db, payload)
    return AuthResponse(token=Token(access_token=access_token), user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)
