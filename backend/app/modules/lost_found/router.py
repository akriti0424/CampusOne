from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.lost_found.schema import (
    LostFoundCreate,
    LostFoundRead,
    MatchRead,
    StatusChange,
    VerificationRequestRead,
    VerificationSubmit,
)
from app.modules.lost_found.service import (
    close_item,
    create_item,
    list_items,
    list_matches,
    resolve_item,
    request_verification,
    verify_item,
)


router = APIRouter(prefix="/api/lost-found", tags=["lost-found"])


@router.get("/items", response_model=list[LostFoundRead])
def read_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_items(db, current_user.id)


@router.post("/items", response_model=LostFoundRead)
def add_item(payload: LostFoundCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item, _matches = create_item(db, current_user.id, payload)
    return item


@router.get("/matches", response_model=list[MatchRead])
def read_matches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_matches(db, current_user.id)


def _require_admin(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.post("/items/{item_id}/verification-request", response_model=VerificationRequestRead)
def ask_verification(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        item, code = request_verification(db, item_id, current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return VerificationRequestRead(item_id=item.id, status=item.status, verification_code=code)


@router.post("/items/{item_id}/verify", response_model=LostFoundRead)
def admin_verify(
    item_id: int,
    payload: VerificationSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    try:
        item = verify_item(db, item_id, payload.verification_code, payload.desk_notes)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return item


@router.post("/items/{item_id}/resolve", response_model=LostFoundRead)
def admin_resolve(
    item_id: int,
    payload: StatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if payload.status != "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolution must set status to resolved")
    try:
        item = resolve_item(db, item_id, None)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return item


@router.post("/items/{item_id}/close", response_model=LostFoundRead)
def admin_close(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    try:
        item = close_item(db, item_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return item
