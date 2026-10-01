"""Quiz service: serves the active quiz and stores scored attempts (Plan.md §9.2).

The quiz itself comes from data/game/ (validated on load); only attempts live in the database.
"""

import random
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QuizAttemptRow
from app.engines.game_data import TRAITS, GameData
from app.engines.matching import ALGORITHM_VERSION, display_scores, raw_totals
from app.schemas.quiz import Quiz, QuizAttempt, QuizOption, QuizQuestion, TraitScore


class InvalidAnswers(ValueError):
    pass


def player_quiz(data: GameData, user_id: UUID) -> Quiz:
    """The active quiz without its trait deltas, options shuffled per player.

    The shuffle is seeded by player and question, so a reload shows the same order.
    """
    questions = []
    for q in data.quiz.questions:
        options = [QuizOption(id=o.id, label=o.label) for o in q.options]
        random.Random(f"{user_id}:{data.quiz.version}:{q.id}").shuffle(options)
        questions.append(QuizQuestion(id=q.id, prompt=q.prompt, options=options))
    return Quiz(version=data.quiz.version, questions=questions)


def trait_scores(data: GameData, answers: dict[str, str]) -> dict[str, float]:
    """Min-max 0-100 trait scores; raises InvalidAnswers for a missing or unknown answer."""
    try:
        scores = display_scores(data.quiz, raw_totals(data.quiz, answers))
    except (ValueError, KeyError) as exc:
        raise InvalidAnswers(str(exc).strip("'\"")) from exc
    return {str(trait): value for trait, value in scores.items()}


def present_traits(data: GameData, scores: dict[str, float]) -> list[TraitScore]:
    defs = {t.id: t for t in data.traits.traits}
    return [
        TraitScore(
            id=t, label=defs[t].label, score=round(scores[t]), low=defs[t].low, high=defs[t].high
        )
        for t in TRAITS
    ]


async def create_attempt(
    session: AsyncSession, data: GameData, user_id: UUID, answers: dict[str, str]
) -> QuizAttempt:
    scores = trait_scores(data, answers)
    row = QuizAttemptRow(
        user_id=user_id,
        quiz_id=data.quiz.version,
        answers=answers,
        trait_scores=scores,
        algorithm_version=ALGORITHM_VERSION,
    )
    session.add(row)
    await session.commit()
    return QuizAttempt(id=row.id, quiz_version=row.quiz_id, traits=present_traits(data, scores))
