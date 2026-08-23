from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.modules.auth.model import PendingRegistration, User
from app.modules.auth.schema import (
    AuthResponse, EmailVerificationSubmit, PasswordChangeRequest, RegistrationResponse,
    ResendVerificationRequest, Token, UserCreate, UserLogin, UserRead,
)
from app.modules.auth.service import (
    authenticate_user, change_user_password, delete_user_by_admin, issue_verification_otp,
    list_all_users_for_admin, register_pending_user, verify_email_otp,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


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


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change_user_password(db, current_user, payload.current_password, payload.new_password)
    return {"message": "Password changed successfully"}


@admin_router.get("/users", response_model=list[UserRead])
def get_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    _ = current_admin
    return [UserRead.model_validate(user) for user in list_all_users_for_admin(db)]


@admin_router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    delete_user_by_admin(db, current_admin, user_id)
    return {"message": "User deleted successfully"}

