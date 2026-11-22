"""Spaced review: cards scheduled with fixed intervals and a daily limit.

Excerpt from app/services/reviews.py (BeyondPy). The rest of the module (the review page
queries, postponing and the daily summary) is omitted.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app import i18n
from app.models import ReviewLog, ReviewState
from app.services import ownership
from app.services.content import (
    ContentNotFound,
    Module,
    ReviewCard,
    list_modules,
    load_cards,
)

# Days until the next review after each correct answer. A wrong answer goes back to the start.
INTERVALS_DAYS = (1, 3, 7, 14, 30, 60, 120, 240)


@dataclass(frozen=True)
class DueCard:
    module: Module
    card: ReviewCard
    state: ReviewState


def now() -> datetime:
    return datetime.now(UTC)


def schedule_lesson_cards(
    session: Session, module: Module, lesson_slug: str, at: datetime | None = None
) -> None:
    """Put the lesson's cards in the schedule (first review tomorrow). Already scheduled: no-op."""
    at = at or now()
    rows = [
        {
            "user_id": ownership.owner(session),
            "module_slug": module.slug,
            "card_slug": card.slug,
            "step": 0,
            "due_at": at + timedelta(days=INTERVALS_DAYS[0]),
        }
        for card in load_cards(module)
        if card.lesson == lesson_slug
    ]
    if rows:
        session.execute(insert(ReviewState).values(rows).on_conflict_do_nothing())
        session.commit()


def due_cards(
    session: Session, at: datetime | None = None, language: str = i18n.SOURCE
) -> list[DueCard]:
    """Cards due now, shortest interval first, then oldest. Removed content is skipped.

    The daily limit cuts this list, so the order decides who waits: the first reviews after a
    lesson (and the cards just missed) come before mature cards.
    """
    at = at or now()
    cards = {
        (module.slug, card.slug): (module, card)
        for module in list_modules(language=language)
        for card in load_cards(module)
    }
    states = session.scalars(
        select(ReviewState)
        .where(ReviewState.due_at <= at)
        .order_by(ReviewState.step, ReviewState.due_at)
    )
    return [
        DueCard(*cards[(state.module_slug, state.card_slug)], state)
        for state in states
        if (state.module_slug, state.card_slug) in cards
    ]


def grade(
    session: Session,
    module_slug: str,
    card_slug: str,
    answer: str,
    correct: bool,
    at: datetime | None = None,
) -> ReviewState:
    """Record the answer and move the card forward (correct) or back to the start (wrong).

    A card that is not due is left as it is: going back to an answered card (browser back
    button, double click) must not move it forward a second time.
    """
    at = at or now()
    state = session.scalars(
        select(ReviewState).where(
            ReviewState.module_slug == module_slug, ReviewState.card_slug == card_slug
        )
    ).first()
    if state is None:
        raise ContentNotFound(f"Card {card_slug!r} is not scheduled")
    if state.due_at > at:
        return state

    state.step = min(state.step + 1, len(INTERVALS_DAYS) - 1) if correct else 0
    state.due_at = at + timedelta(days=INTERVALS_DAYS[state.step])
    state.last_reviewed_at = at
    session.add(
        ReviewLog(
            module_slug=module_slug,
            card_slug=card_slug,
            answer=answer,
            correct=correct,
            reviewed_at=at,
        )
    )
    session.commit()
    return state
