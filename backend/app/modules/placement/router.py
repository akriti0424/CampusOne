from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.placement.model import (
    PlacementAnswer,
    PlacementAttempt,
    PlacementProgress,
    PlacementQuestion,
    PlacementTest,
)
from app.modules.placement.schema import (
    AnswerSubmission,
    AttemptAnswerSubmission,
    QuestionProgressUpdate,
    TestGenerationRequest,
)


router = APIRouter(prefix="/api/placement", tags=["placement"])

PLACEMENT_SYLLABUS = {
    "Quantitative Aptitude & DI": [
        "Number Systems", "HCF/LCM", "Percentages", "Profit & Loss", "Ratio & Proportion",
        "Time & Work", "Time-Speed-Distance", "Simple & Compound Interest",
        "Permutation & Combination", "Probability", "Data Interpretation",
    ],
    "Logical Reasoning & Verbal Ability": [
        "Seating Arrangements", "Puzzles", "Blood Relations", "Syllogisms", "Coding-Decoding",
        "Number/Letter Series", "Direction Sense", "Reading Comprehension", "Grammar/Sentence Correction",
    ],
    "CS Fundamentals": [
        "DBMS & SQL", "Operating Systems", "Computer Networks", "OOPs & Output Prediction",
    ],
    "DSA & Coding Assessment": [
        "Arrays", "Strings", "Hashing", "Two Pointers", "Sliding Window", "Recursion/Backtracking",
        "Linked Lists", "Stacks/Queues", "Trees", "Graphs", "Dynamic Programming",
    ],
}

PLACEMENT_CURRICULUM = [
    {
        "category": "Core Subjects",
        "description": "Computer science fundamentals commonly tested in technical OAs.",
        "subjects": [
            {"name": "DBMS & SQL", "topics": ["ER model", "Keys", "Normalization", "ACID properties", "Transactions", "Indexing", "Joins", "Query output prediction"]},
            {"name": "Operating Systems", "topics": ["Processes and threads", "CPU scheduling", "Deadlocks", "Memory management", "Paging", "Semaphores", "Synchronization"]},
            {"name": "Computer Networks", "topics": ["OSI and TCP/IP layers", "Subnetting", "HTTP/HTTPS", "DNS", "Routing protocols", "TCP vs UDP"]},
            {"name": "OOPs", "topics": ["Classes and objects", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction", "References and pointers", "Output prediction and debugging"]},
        ],
    },
    {
        "category": "Programming & DSA",
        "description": "Coding patterns and language fundamentals for programming rounds.",
        "subjects": [
            {"name": "Programming Languages", "topics": ["C/C++ fundamentals", "Java fundamentals", "Python fundamentals", "Pointers and references", "STL/collections", "Input/output and debugging"]},
            {"name": "Data Structures", "topics": ["Arrays", "Strings", "Hashing", "Linked Lists", "Stacks and Queues", "Trees", "Graphs"]},
            {"name": "Algorithms", "topics": ["Two pointers", "Sliding window", "Recursion and backtracking", "Sorting and searching", "Greedy algorithms", "Dynamic programming", "Complexity analysis"]},
        ],
    },
    {
        "category": "Logical Reasoning",
        "description": "Reasoning patterns used in campus aptitude and OA sections.",
        "subjects": [
            {"name": "Analytical Reasoning", "topics": ["Seating arrangements", "Puzzles", "Blood relations", "Syllogisms", "Coding-decoding", "Number and letter series", "Direction sense"]},
        ],
    },
    {
        "category": "English & Verbal Ability",
        "description": "Language accuracy, comprehension, and communication readiness.",
        "subjects": [
            {"name": "Verbal Ability", "topics": ["Reading comprehension", "Grammar", "Sentence correction", "Para jumbles", "Vocabulary", "Synonyms and antonyms", "Fill in the blanks"]},
        ],
    },
    {
        "category": "Quantitative Aptitude",
        "description": "Numerical reasoning and data interpretation for placement tests.",
        "subjects": [
            {"name": "Aptitude", "topics": ["Number systems", "HCF/LCM", "Percentages", "Profit and loss", "Ratio and proportion", "Time and work", "Time-speed-distance", "Simple and compound interest", "Permutation and combination", "Probability", "Data interpretation"]},
        ],
    },
]

PLACEMENT_CHEATSHEETS = [
    {"category": "Quantitative Aptitude", "title": "Percentages, Profit & Loss", "items": ["Percentage change = (new - old) / old × 100", "Successive changes a% and b% = a + b + ab/100", "Profit% = profit / cost price × 100", "Selling price = cost price × (1 + profit%)"]},
    {"category": "Quantitative Aptitude", "title": "Time, Work & Speed", "items": ["Work = rate × time", "Combined work rate = sum of individual rates", "Distance = speed × time", "For equal distances, average speed = 2ab / (a + b)"]},
    {"category": "Logical Reasoning", "title": "Series & Syllogisms", "items": ["Check differences, ratios, squares, cubes, and alternating patterns", "For syllogisms, convert statements to set relationships before testing conclusions", "Do not infer a converse unless it is explicitly stated"]},
    {"category": "Core Subjects", "title": "DBMS & SQL", "items": ["Atomicity: all-or-nothing transaction", "Consistency: valid state before and after transaction", "Isolation: concurrent transactions do not interfere", "Durability: committed data survives failures", "Indexing improves reads but adds write/storage cost"]},
    {"category": "Core Subjects", "title": "OS & Networks", "items": ["Deadlock requires mutual exclusion, hold-and-wait, no preemption, and circular wait", "DNS resolves names to IP addresses", "TCP is connection-oriented; UDP is connectionless", "Paging maps virtual pages to physical frames"]},
    {"category": "Programming & DSA", "title": "Complexity Patterns", "items": ["Hash-map lookup is O(1) average", "Sort + two pointers is commonly O(n log n)", "Sliding window is usually O(n)", "BFS/DFS on adjacency lists is O(V + E)", "Dynamic programming often trades O(n) or O(n²) memory for repeated subproblem reuse"]},
]


def question_payload(db: Session, question: PlacementQuestion, user_id: int) -> dict[str, object]:
    progress = db.query(PlacementProgress).filter_by(user_id=user_id, question_id=question.id).first()
    return {
        "id": question.id,
        "pillar": question.pillar,
        "topic": question.topic,
        "format": question.question_format,
        "prompt": question.prompt,
        "options": question.options,
        "difficulty": question.difficulty,
        "company_tags": question.company_tags,
        "is_top_question": question.is_top_question,
        "top_rank": question.top_rank,
        "is_quiz_question": question.is_quiz_question,
        "constraints": question.constraints,
        "sample_input": question.sample_input,
        "sample_output": question.sample_output,
        "hints": question.hints,
        "optimal_approach": question.optimal_approach,
        "time_complexity": question.time_complexity,
        "space_complexity": question.space_complexity,
        "status": progress.status if progress else "unsolved",
        "bookmarked": progress.bookmarked if progress else False,
    }


def ensure_progress(db: Session, user_id: int, question_id: int) -> PlacementProgress:
    progress = db.query(PlacementProgress).filter_by(user_id=user_id, question_id=question_id).first()
    if progress:
        return progress
    progress = PlacementProgress(user_id=user_id, question_id=question_id)
    db.add(progress)
    db.flush()
    return progress


@router.get("/questions")
def list_questions(
    pillar: str | None = None,
    topic: str | None = None,
    difficulty: str | None = None,
    company: str | None = None,
    question_format: str | None = Query(default=None, alias="format"),
    bookmarked: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PlacementQuestion)
    if pillar:
        query = query.filter(PlacementQuestion.pillar == pillar)
    if topic:
        query = query.filter(PlacementQuestion.topic == topic)
    if difficulty:
        query = query.filter(PlacementQuestion.difficulty == difficulty)
    if question_format:
        query = query.filter(PlacementQuestion.question_format == question_format)
    if company:
        query = query.filter(PlacementQuestion.company_tags.contains([company]))
    if bookmarked is not None:
        query = query.join(PlacementProgress, PlacementProgress.question_id == PlacementQuestion.id).filter(
            PlacementProgress.user_id == current_user.id,
            PlacementProgress.bookmarked == bookmarked,
        )
    return [question_payload(db, question, current_user.id) for question in query.order_by(PlacementQuestion.id).all()]


@router.get("/metadata")
def question_metadata(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    questions = db.query(PlacementQuestion).all()
    return {
        "pillars": list(PLACEMENT_SYLLABUS),
        "topics": sorted({topic for topics in PLACEMENT_SYLLABUS.values() for topic in topics} | {question.topic for question in questions}),
        "difficulties": ["Easy", "Medium", "Hard"],
        "companies": sorted({tag for question in questions for tag in question.company_tags}),
    }


@router.get("/curriculum")
def curriculum(current_user: User = Depends(get_current_user)):
    return {"categories": PLACEMENT_CURRICULUM, "cheatsheets": PLACEMENT_CHEATSHEETS}


@router.get("/top-questions")
def top_questions(
    topic: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PlacementQuestion).filter(PlacementQuestion.is_top_question.is_(True))
    if topic:
        query = query.filter(PlacementQuestion.topic == topic)
    questions = query.order_by(PlacementQuestion.top_rank, PlacementQuestion.id).limit(50).all()
    return [question_payload(db, question, current_user.id) for question in questions]


@router.get("/quiz-questions")
def quiz_questions(
    topic: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PlacementQuestion).filter(PlacementQuestion.is_quiz_question.is_(True))
    if topic:
        query = query.filter(PlacementQuestion.topic == topic)
    questions = query.order_by(PlacementQuestion.id).all()
    return [question_payload(db, question, current_user.id) for question in questions]


@router.post("/questions/{question_id}/answer")
def submit_answer(
    question_id: int,
    payload: AnswerSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = db.get(PlacementQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    progress = ensure_progress(db, current_user.id, question_id)
    is_correct = payload.answer.strip().lower() == question.correct_answer.strip().lower()
    progress.attempts += 1
    progress.correct_attempts += int(is_correct)
    if is_correct:
        progress.status = "solved"
    elif progress.status == "unsolved":
        progress.status = "needs_revision"
    db.commit()
    return {
        "correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "status": progress.status,
    }


@router.patch("/questions/{question_id}/progress")
def update_progress(
    question_id: int,
    payload: QuestionProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not db.get(PlacementQuestion, question_id):
        raise HTTPException(status_code=404, detail="Question not found")
    progress = ensure_progress(db, current_user.id, question_id)
    progress.status = payload.status
    if payload.bookmarked is not None:
        progress.bookmarked = payload.bookmarked
    db.commit()
    return {"status": progress.status, "bookmarked": progress.bookmarked}


@router.get("/tests")
def list_tests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tests = db.query(PlacementTest).order_by(PlacementTest.id.desc()).all()
    return [
        {
            "id": test.id,
            "title": test.title,
            "company": test.company,
            "duration_minutes": test.duration_minutes,
            "negative_marking": test.negative_marking,
            "section_switching": test.section_switching,
            "question_count": len(test.question_ids),
        }
        for test in tests
    ]


@router.post("/tests/generate")
def generate_test(
    payload: TestGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    questions = db.query(PlacementQuestion).all()
    selected: list[PlacementQuestion] = []
    for pillar in sorted({question.pillar for question in questions}):
        pool = [question for question in questions if question.pillar == pillar]
        selected.extend(random.sample(pool, min(payload.questions_per_pillar, len(pool))))
    if not selected:
        raise HTTPException(status_code=400, detail="Question bank is empty")
    test = PlacementTest(
        title=f"{payload.company} OA Simulator",
        company=payload.company,
        duration_minutes=payload.duration_minutes,
        negative_marking=payload.negative_marking,
        section_switching=payload.section_switching,
        question_ids=[question.id for question in selected],
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return {"id": test.id, "title": test.title, "question_count": len(selected), "duration_minutes": test.duration_minutes}


@router.post("/tests/{test_id}/attempts")
def start_attempt(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = db.get(PlacementTest, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    attempt = PlacementAttempt(user_id=current_user.id, test_id=test.id, total_questions=len(test.question_ids))
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    questions = [db.get(PlacementQuestion, question_id) for question_id in test.question_ids]
    return {"attempt_id": attempt.id, "test": {"id": test.id, "title": test.title, "duration_minutes": test.duration_minutes, "negative_marking": test.negative_marking}, "questions": [question_payload(db, question, current_user.id) for question in questions if question]}


@router.post("/attempts/{attempt_id}/answers")
def save_attempt_answer(
    attempt_id: int,
    payload: AttemptAnswerSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(PlacementAttempt).filter_by(id=attempt_id, user_id=current_user.id).first()
    if not attempt or attempt.status != "in_progress":
        raise HTTPException(status_code=404, detail="Active attempt not found")
    question = db.get(PlacementQuestion, payload.question_id)
    test = db.get(PlacementTest, attempt.test_id)
    if datetime.now(timezone.utc).replace(tzinfo=None) > attempt.started_at.replace(tzinfo=None) + timedelta(minutes=test.duration_minutes):
        attempt.status = "expired"
        db.commit()
        raise HTTPException(status_code=408, detail="This OA attempt has expired")
    if not question or payload.question_id not in test.question_ids:
        raise HTTPException(status_code=400, detail="Question is not part of this test")
    answer = db.query(PlacementAnswer).filter_by(attempt_id=attempt.id, question_id=question.id).first()
    if not answer:
        answer = PlacementAnswer(attempt_id=attempt.id, question_id=question.id, answer=payload.answer, time_spent_seconds=payload.time_spent_seconds)
        db.add(answer)
    else:
        answer.answer = payload.answer
        answer.time_spent_seconds = payload.time_spent_seconds
    answer.is_correct = payload.answer.strip().lower() == question.correct_answer.strip().lower()
    db.commit()
    return {"saved": True, "correct": answer.is_correct}


@router.post("/attempts/{attempt_id}/complete")
def complete_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(PlacementAttempt).filter_by(id=attempt_id, user_id=current_user.id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.status == "completed":
        return attempt_analytics(db, attempt, current_user.id)
    test = db.get(PlacementTest, attempt.test_id)
    if datetime.now(timezone.utc).replace(tzinfo=None) > attempt.started_at.replace(tzinfo=None) + timedelta(minutes=test.duration_minutes):
        attempt.status = "expired"
        attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=408, detail="This OA attempt has expired")
    answers = db.query(PlacementAnswer).filter_by(attempt_id=attempt.id).all()
    correct = sum(answer.is_correct for answer in answers)
    wrong = sum(not answer.is_correct for answer in answers)
    attempt.status = "completed"
    attempt.completed_at = datetime.now(timezone.utc)
    attempt.correct_answers = correct
    attempt.wrong_answers = wrong
    attempt.score = correct - (wrong * 0.25 if test.negative_marking else 0)
    attempt.time_spent_seconds = sum(answer.time_spent_seconds for answer in answers)
    db.commit()
    return attempt_analytics(db, attempt, current_user.id)


@router.get("/attempts/{attempt_id}/analytics")
def get_attempt_analytics(attempt_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attempt = db.query(PlacementAttempt).filter_by(id=attempt_id, user_id=current_user.id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt_analytics(db, attempt, current_user.id)


def attempt_analytics(db: Session, attempt: PlacementAttempt, user_id: int) -> dict[str, object]:
    answers = db.query(PlacementAnswer).filter_by(attempt_id=attempt.id).all()
    by_id = {question.id: question for question in db.query(PlacementQuestion).filter(PlacementQuestion.id.in_([answer.question_id for answer in answers])).all()}
    sections: dict[str, dict[str, int]] = {}
    for answer in answers:
        pillar = by_id[answer.question_id].pillar
        section = sections.setdefault(pillar, {"attempted": 0, "correct": 0, "time_spent_seconds": 0})
        section["attempted"] += 1
        section["correct"] += int(answer.is_correct)
        section["time_spent_seconds"] += answer.time_spent_seconds
    topic_wrong: dict[str, int] = {}
    for answer in answers:
        question = by_id.get(answer.question_id)
        if question and not answer.is_correct:
            topic_wrong[question.topic] = topic_wrong.get(question.topic, 0) + 1
    weak_topics = sorted(topic_wrong.items(), key=lambda item: item[1], reverse=True)[:5]
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "score": attempt.score,
        "total_questions": attempt.total_questions,
        "correct_answers": attempt.correct_answers,
        "wrong_answers": attempt.wrong_answers,
        "time_spent_seconds": attempt.time_spent_seconds,
        "sections": sections,
        "weak_topics": [{"topic": topic, "wrong_answers": wrong} for topic, wrong in weak_topics if wrong],
    }


@router.get("/readiness")
def readiness(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    questions = db.query(PlacementQuestion).all()
    progress = db.query(PlacementProgress).filter_by(user_id=current_user.id).all()
    progress_by_question = {item.question_id: item for item in progress}
    summary: dict[str, dict[str, int]] = {}
    for question in questions:
        item = summary.setdefault(question.pillar, {"total": 0, "solved": 0, "needs_revision": 0, "unsolved": 0})
        item["total"] += 1
        status = progress_by_question.get(question.id).status if question.id in progress_by_question else "unsolved"
        item[status] += 1
    return {"summary": summary, "streak_days": 0, "total_solved": sum(item["solved"] for item in summary.values())}
