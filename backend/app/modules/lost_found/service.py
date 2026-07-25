from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy.orm import Session

from app.modules.lost_found.model import LostFoundItem, LostFoundMatch
from app.modules.lost_found.schema import LostFoundCreate


def _tokenize(text: str) -> set[str]:
    return {word.strip(".,!?;:()[]{}\"'`").lower() for word in text.split() if len(word.strip()) > 2}


def _generate_verification_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def _hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def score_similarity(left: LostFoundCreate | LostFoundItem, right: LostFoundItem) -> float:
    left_text = f"{left.title} {left.description} {left.location}".lower()
    right_text = f"{right.title} {right.description} {right.location}".lower()
    left_tokens = _tokenize(left_text)
    right_tokens = _tokenize(right_text)
    if not left_tokens or not right_tokens:
        return 0.0

    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return round(overlap / union, 3)


def create_item(db: Session, owner_id: int, payload: LostFoundCreate) -> tuple[LostFoundItem, list[LostFoundMatch]]:
    item = LostFoundItem(
        owner_id=owner_id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        image_url=payload.image_url,
        location=payload.location.strip(),
        kind=payload.kind,
    )
    db.add(item)
    db.flush()

    opposite_kind = "found" if item.kind == "lost" else "lost"
    candidates = db.query(LostFoundItem).filter(LostFoundItem.kind == opposite_kind).all()
    matches: list[LostFoundMatch] = []

    for candidate in candidates:
        score = score_similarity(item, candidate)
        if score >= 0.25:
            match = LostFoundMatch(
                source_item_id=item.id,
                candidate_item_id=candidate.id,
                score=score,
                status="suggested",
            )
            db.add(match)
            matches.append(match)

    item.similarity_score = max((match.score for match in matches), default=0.0)
    db.commit()
    db.refresh(item)
    for match in matches:
        db.refresh(match)
    return item, matches


def list_items(db: Session, owner_id: int) -> list[LostFoundItem]:
    return (
        db.query(LostFoundItem)
        .filter(LostFoundItem.owner_id == owner_id)
        .order_by(LostFoundItem.created_at.desc())
        .all()
    )


def list_matches(db: Session, owner_id: int) -> list[LostFoundMatch]:
    source_items = db.query(LostFoundItem.id).filter(LostFoundItem.owner_id == owner_id).subquery()
    return (
        db.query(LostFoundMatch)
        .filter(LostFoundMatch.source_item_id.in_(source_items))
        .order_by(LostFoundMatch.created_at.desc())
        .all()
    )


def request_verification(db: Session, item_id: int, owner_id: int) -> tuple[LostFoundItem, str]:
    item = db.query(LostFoundItem).filter(LostFoundItem.id == item_id, LostFoundItem.owner_id == owner_id).first()
    if not item:
        raise ValueError("Item not found")

    code = _generate_verification_code()
    item.verification_code_hash = _hash_verification_code(code)
    item.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    item.status = "matched"
    db.commit()
    db.refresh(item)
    return item, code


def verify_item(db: Session, item_id: int, verification_code: str, desk_notes: str | None) -> LostFoundItem:
    item = db.query(LostFoundItem).filter(LostFoundItem.id == item_id).first()
    if not item:
        raise ValueError("Item not found")
    if not item.verification_code_hash or not item.verification_code_expires_at:
        raise ValueError("Verification has not been requested")
    if item.verification_code_expires_at < datetime.now(timezone.utc):
        raise ValueError("Verification code expired")
    if _hash_verification_code(verification_code) != item.verification_code_hash:
        raise ValueError("Invalid verification code")

    item.status = "verified"
    item.verified_at = datetime.now(timezone.utc)
    item.desk_notes = desk_notes
    db.commit()
    db.refresh(item)
    return item


def resolve_item(db: Session, item_id: int, desk_notes: str | None) -> LostFoundItem:
    item = db.query(LostFoundItem).filter(LostFoundItem.id == item_id).first()
    if not item:
        raise ValueError("Item not found")

    item.status = "resolved"
    item.resolved_at = datetime.now(timezone.utc)
    item.desk_notes = desk_notes or item.desk_notes
    db.commit()
    db.refresh(item)
    return item


def close_item(db: Session, item_id: int) -> LostFoundItem:
    item = db.query(LostFoundItem).filter(LostFoundItem.id == item_id).first()
    if not item:
        raise ValueError("Item not found")

    item.status = "closed"
    item.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item
