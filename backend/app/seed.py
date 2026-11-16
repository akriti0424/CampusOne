from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.auth.model import User
from app.modules.chat.model import ChatMessage
from app.modules.lost_found.model import LostFoundItem, LostFoundMatch
from app.modules.product.model import Product
from app.modules.placement.model import PlacementQuestion, PlacementTest
from app.modules.placement.router import PLACEMENT_CURRICULUM


def _placement_topics() -> list[tuple[str, str, str]]:
    return [
        (category["category"], subject["name"], topic)
        for category in PLACEMENT_CURRICULUM
        for subject in category["subjects"]
        for topic in subject["topics"]
    ]


def _ensure_top_question_sets(db: Session) -> None:
    company_rotation = ["TCS", "Infosys", "Accenture", "Wipro", "Cognizant", "Amazon", "Microsoft"]
    for category, subject, topic in _placement_topics():
        topic_questions = [
            question
            for question in db.query(PlacementQuestion).all()
            if question.topic.casefold() == topic.casefold()
        ]

        # Older seed data did not distinguish learning quizzes from Top 50
        # questions. Keep the original questions as the separate quiz set and
        # retain only generated "Top OA Question" records in Top 50.
        for question in topic_questions:
            is_generated_top = "Top OA Question" in question.prompt
            if not is_generated_top:
                question.is_top_question = False
                question.top_rank = None
                question.is_quiz_question = True

        top_questions = [question for question in topic_questions if question.is_top_question]
        top_questions.sort(key=lambda question: (question.top_rank is None, question.top_rank or question.id))
        for rank, question in enumerate(top_questions[:50], start=1):
            question.is_top_question = True
            question.top_rank = rank

        existing_count = min(len(top_questions), 50)
        for rank in range(existing_count + 1, 51):
            db.add(
                PlacementQuestion(
                    pillar=category,
                    topic=topic,
                    question_format="mcq",
                    prompt=f"{topic} — Top OA Question {rank}: Which preparation approach is most appropriate for this topic?",
                    options=[
                        f"Apply the core {topic} concept to a timed problem",
                        "Skip the topic entirely",
                        "Memorize unrelated facts",
                        "Only read the question statement",
                    ],
                    correct_answer=f"Apply the core {topic} concept to a timed problem",
                    explanation=f"Placement OAs test practical application of {topic}. Revise the concept, solve a timed example, and review the mistake pattern.",
                    difficulty=["Easy", "Medium", "Hard"][(rank - 1) % 3],
                    company_tags=[company_rotation[(rank - 1) % len(company_rotation)]],
                    is_top_question=True,
                    top_rank=rank,
                    is_quiz_question=False,
                )
            )
        db.flush()

        topic_questions = [
            question
            for question in db.query(PlacementQuestion).all()
            if question.topic.casefold() == topic.casefold()
        ]
        quiz_questions = [question for question in topic_questions if question.is_quiz_question]
        for rank in range(len(quiz_questions) + 1, 11):
            db.add(
                PlacementQuestion(
                    pillar=category,
                    topic=topic,
                    question_format="mcq",
                    prompt=f"{topic} Quiz Question {rank}: Which action best improves your accuracy in this topic?",
                    options=[
                        f"Solve varied {topic} problems and review mistakes",
                        "Guess without checking the concept",
                        "Skip all timed practice",
                        "Memorize answers without understanding",
                    ],
                    correct_answer=f"Solve varied {topic} problems and review mistakes",
                    explanation=f"Quiz practice for {topic} should combine varied questions, timed solving, and review of mistakes.",
                    difficulty=["Easy", "Medium", "Hard"][(rank - 1) % 3],
                    company_tags=[company_rotation[(rank - 1) % len(company_rotation)]],
                    is_top_question=False,
                    is_quiz_question=True,
                )
            )


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

        if not db.query(PlacementQuestion).first():
            db.add_all(
                [
                    PlacementQuestion(
                        pillar="Quantitative Aptitude & DI", topic="Percentages", question_format="mcq",
                        prompt="A price is increased by 20% and then discounted by 20%. What is the net change?",
                        options=["No change", "4% decrease", "4% increase", "2% decrease"], correct_answer="4% decrease",
                        explanation="Take 100: 100 × 1.2 × 0.8 = 96, so the net change is a 4% decrease.",
                        difficulty="Easy", company_tags=["TCS", "Infosys", "Accenture"],
                    ),
                    PlacementQuestion(
                        pillar="Quantitative Aptitude & DI", topic="Time & Work", question_format="mcq",
                        prompt="A can finish a task in 12 days and B in 18 days. How long do they take together?",
                        options=["6 days", "7.2 days", "8 days", "9 days"], correct_answer="7.2 days",
                        explanation="Combined rate is 1/12 + 1/18 = 5/36, so time is 36/5 = 7.2 days.",
                        difficulty="Medium", company_tags=["Wipro", "Cognizant"],
                    ),
                    PlacementQuestion(
                        pillar="Logical Reasoning & Verbal Ability", topic="Syllogisms", question_format="mcq",
                        prompt="Statements: All coders are readers. Some readers are athletes. Which conclusion definitely follows?",
                        options=["All coders are athletes", "Some athletes are readers", "No reader is a coder", "All athletes are coders"],
                        correct_answer="Some athletes are readers", explanation="The second statement directly establishes that some readers are athletes.",
                        difficulty="Easy", company_tags=["Capgemini", "Accenture"],
                    ),
                    PlacementQuestion(
                        pillar="Logical Reasoning & Verbal Ability", topic="Number/Letter Series", question_format="mcq",
                        prompt="Find the next number: 2, 6, 12, 20, 30, ?",
                        options=["36", "40", "42", "44"], correct_answer="42",
                        explanation="Terms are n(n+1): 1×2, 2×3, ..., 6×7 = 42.",
                        difficulty="Easy", company_tags=["TCS", "Infosys"],
                    ),
                    PlacementQuestion(
                        pillar="CS Fundamentals", topic="DBMS & SQL", question_format="mcq",
                        prompt="Which property ensures a transaction is completed entirely or not at all?",
                        options=["Consistency", "Isolation", "Atomicity", "Durability"], correct_answer="Atomicity",
                        explanation="Atomicity makes a transaction indivisible: all operations commit or all roll back.",
                        difficulty="Easy", company_tags=["Amazon", "Microsoft", "TCS"],
                    ),
                    PlacementQuestion(
                        pillar="CS Fundamentals", topic="Operating Systems", question_format="mcq",
                        prompt="Which scheduling algorithm can cause starvation without aging?",
                        options=["FCFS", "Round Robin", "Priority Scheduling", "FIFO"], correct_answer="Priority Scheduling",
                        explanation="Low-priority processes may wait indefinitely when higher-priority work keeps arriving.",
                        difficulty="Medium", company_tags=["Infosys", "Wipro"],
                    ),
                    PlacementQuestion(
                        pillar="CS Fundamentals", topic="Computer Networks", question_format="mcq",
                        prompt="Which protocol translates a domain name into an IP address?",
                        options=["HTTP", "DNS", "ARP", "FTP"], correct_answer="DNS",
                        explanation="The Domain Name System resolves host names to IP addresses.",
                        difficulty="Easy", company_tags=["Cognizant", "Accenture"],
                    ),
                    PlacementQuestion(
                        pillar="CS Fundamentals", topic="OOPs & Output Prediction", question_format="mcq",
                        prompt="Which OOP concept allows a subclass to provide its own implementation of a parent method?",
                        options=["Encapsulation", "Overloading", "Overriding", "Abstraction"], correct_answer="Overriding",
                        explanation="Method overriding replaces inherited behavior at runtime.",
                        difficulty="Easy", company_tags=["TCS", "Capgemini"],
                    ),
                    PlacementQuestion(
                        pillar="DSA & Coding Assessment", topic="Arrays", question_format="coding",
                        prompt="Given an integer array and a target, return the indices of two numbers that sum to the target.",
                        constraints="1 <= n <= 100000; exactly one solution exists.",
                        sample_input="[2, 7, 11, 15], target = 9", sample_output="[0, 1]",
                        hints=["Store previously seen values in a hash map."],
                        optimal_approach="Scan once and look up target - current value in a hash map.",
                        time_complexity="O(n)", space_complexity="O(n)", correct_answer="hash-map",
                        difficulty="Easy", company_tags=["Amazon", "Google", "Microsoft"],
                    ),
                    PlacementQuestion(
                        pillar="DSA & Coding Assessment", topic="Sliding Window", question_format="coding",
                        prompt="Find the length of the longest substring without repeating characters.",
                        constraints="0 <= length(s) <= 50000.", sample_input='"abcabcbb"', sample_output="3",
                        hints=["Keep a left pointer and the last index of each character."],
                        optimal_approach="Use a moving window and a map of last-seen character positions.",
                        time_complexity="O(n)", space_complexity="O(min(n, alphabet))", correct_answer="sliding-window",
                        difficulty="Medium", company_tags=["Amazon", "Microsoft", "Adobe"],
                    ),
                    PlacementQuestion(
                        pillar="DSA & Coding Assessment", topic="Dynamic Programming", question_format="coding",
                        prompt="Return the maximum sum of non-adjacent elements in an array.",
                        constraints="1 <= n <= 100000.", sample_input="[2, 7, 9, 3, 1]", sample_output="12",
                        hints=["At every index choose skip or take current plus dp[i-2]."],
                        optimal_approach="Maintain the best result ending at the previous two positions.",
                        time_complexity="O(n)", space_complexity="O(1)", correct_answer="dp", difficulty="Medium",
                        company_tags=["Google", "Amazon", "Flipkart"],
                    ),
                ]
            )
            db.flush()
            questions = db.query(PlacementQuestion).all()
            db.add(
                PlacementTest(
                    title="CampusOne Mixed OA Starter",
                    company="Campus Practice",
                    duration_minutes=60,
                    negative_marking=True,
                    section_switching=True,
                    question_ids=[question.id for question in questions],
                )
            )

        _ensure_top_question_sets(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
