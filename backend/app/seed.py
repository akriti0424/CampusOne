from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.auth.model import User
from app.modules.chat.model import ChatMessage
from app.modules.lost_found.model import LostFoundItem, LostFoundMatch
from app.modules.product.model import Product


def _get_or_create_user(db: Session, email: str, defaults: dict[str, object]) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        return user

    user = User(
        full_name=defaults["full_name"],
        scholar_id=defaults["scholar_id"],
        branch=defaults["branch"],
        email=email,
        password_hash=hash_password(defaults["password"]),
        role=defaults.get("role", "student"),
        is_verified=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        admin = _get_or_create_user(
            db,
            "admin@stu.manit.ac.in",
            {
                "full_name": "Campus Admin",
                "scholar_id": "MANIT-ADMIN-01",
                "branch": "Admin",
                "password": "Admin1234!",
                "role": "admin",
            },
        )
        student = _get_or_create_user(
            db,
            "ananya@stu.manit.ac.in",
            {
                "full_name": "Ananya Sharma",
                "scholar_id": "2021CS101",
                "branch": "CSE",
                "password": "Student1234!",
                "role": "student",
            },
        )

        if not db.query(Product).first():
            db.add_all(
                [
                    Product(
                        title="Calculus Notes Bundle",
                        description="Clean handwritten notes for first-year math. Good condition.",
                        price=180.0,
                        category="Books",
                        negotiable=True,
                        seller_id=student.id,
                        image_url=None,
                        status="available",
                    ),
                    Product(
                        title="Study Table Lamp",
                        description="Warm light lamp used in hostel room for a semester.",
                        price=420.0,
                        category="Hostel Items",
                        negotiable=False,
                        seller_id=admin.id,
                        image_url=None,
                        status="available",
                    ),
                ]
            )

        if not db.query(LostFoundItem).first():
            lost = LostFoundItem(
                title="Blue Wallet",
                description="Lost blue wallet near the canteen with MANIT ID card inside.",
                image_url=None,
                location="Canteen side",
                kind="lost",
                status="matched",
                owner_id=student.id,
                similarity_score=0.71,
            )
            found = LostFoundItem(
                title="Blue Wallet Found",
                description="Found a blue wallet with student card near the canteen seating area.",
                image_url=None,
                location="Canteen side",
                kind="found",
                status="verified",
                owner_id=admin.id,
                similarity_score=0.71,
                verified_at=datetime.now(timezone.utc),
                resolved_at=datetime.now(timezone.utc),
                desk_notes="Matched at desk and verified with OTP.",
            )
            db.add_all([lost, found])
            db.flush()
            db.add(
                LostFoundMatch(
                    source_item_id=lost.id,
                    candidate_item_id=found.id,
                    score=0.71,
                    status="verified",
                )
            )

        if not db.query(ChatMessage).first():
            db.add_all(
                [
                    ChatMessage(
                        room_name="general",
                        display_name="Campus Admin",
                        message="Welcome to CampusOne. Keep the community clean and helpful.",
                        is_system=True,
                        author_id=admin.id,
                    ),
                    ChatMessage(
                        room_name="general",
                        display_name="Ananya (CSE)",
                        message="Is the library open after 8 pm today?",
                        author_id=student.id,
                    ),
                ]
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
