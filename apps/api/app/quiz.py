"""Quiz service: serves the quiz and encounter, stores and completes attempts (Plan.md §9.2-9.4).

The quiz itself comes from data/game/ (validated on load); only attempts live in the database.
"""

import random
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QuizAttemptRow, SpeciesRow
from app.engines import matching
from app.engines.game_data import TRAITS, GameData
from app.engines.matching import ALGORITHM_VERSION, display_scores, raw_totals
from app.schemas.quiz import (
    DragonMatch,
    Encounter,
    EncounterChoices,
    EncounterScene,
    Quiz,
    QuizAttempt,
    QuizAttemptDetail,
    QuizMatch,
    QuizOption,
    QuizQuestion,
    TraitScore,
)


class InvalidAnswers(ValueError):
    pass


class AttemptNotFound(LookupError):
    pass


class AttemptConflict(ValueError):
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


# ── encounter ────────────────────────────────────────────────────────────────


def _shuffled(options: list[QuizOption], seed: str) -> list[QuizOption]:
    random.Random(seed).shuffle(options)
    return options


def player_encounter(data: GameData, user_id: UUID) -> Encounter:
    """The three scenes without what each option means (approach, food, nudges)."""
    enc = data.encounter
    scenes = [
        (scene_id, scene.prompt, [QuizOption(id=o.id, label=o.label) for o in scene.options])
        for scene_id, scene in (
            ("first_contact", enc.scenes.first_contact),
            ("offering", enc.scenes.offering),
            ("startle", enc.scenes.startle),
        )
    ]
    return Encounter(
        version=enc.version,
        scenes=[
            EncounterScene(
                id=scene_id,
                prompt=prompt,
                options=_shuffled(options, f"{user_id}:{enc.version}:{scene_id}"),
            )
            for scene_id, prompt, options in scenes
        ],
    )


async def own_attempt(
    session: AsyncSession, user_id: UUID, attempt_id: UUID, *, lock: bool = False
) -> QuizAttemptRow:
    query = select(QuizAttemptRow).where(
        QuizAttemptRow.id == attempt_id, QuizAttemptRow.user_id == user_id
    )
    row = (await session.execute(query.with_for_update() if lock else query)).scalar_one_or_none()
    if row is None:
        # Someone else's attempt looks exactly like a missing one.
        raise AttemptNotFound(f"No quiz attempt {attempt_id}")
    return row


async def _present_match(
    session: AsyncSession, data: GameData, ranking: list[dict[str, Any]]
) -> QuizMatch:
    ids = [r["species_id"] for r in ranking]
    rows = await session.execute(
        select(SpeciesRow.id, SpeciesRow.name).where(SpeciesRow.id.in_(ids))
    )
    names = {species_id: name for species_id, name in rows}
    profiles = {s.id: s for s in data.species}
    matches = [
        DragonMatch(
            species_id=r["species_id"],
            # The canon name if the catalog is loaded, else a readable fallback.
            name=names.get(r["species_id"], r["species_id"].replace("_", " ").title()),
            rarity=profiles[r["species_id"]].rarity,
            summary=profiles[r["species_id"]].summary,
            compatibility=r["compatibility"],
            explanation=r["explanation"],
        )
        for r in ranking
    ]
    return QuizMatch(top=matches[0], runners_up=matches[1:])


async def _detail(session: AsyncSession, data: GameData, row: QuizAttemptRow) -> QuizAttemptDetail:
    return QuizAttemptDetail(
        id=row.id,
        quiz_version=row.quiz_id,
        traits=present_traits(data, row.trait_scores or {}),
        match=await _present_match(session, data, row.ranking) if row.ranking else None,
    )


async def get_attempt(
    session: AsyncSession, data: GameData, user_id: UUID, attempt_id: UUID
) -> QuizAttemptDetail:
    return await _detail(session, data, await own_attempt(session, user_id, attempt_id))


def _check_choices(data: GameData, choices: EncounterChoices) -> None:
    scenes = data.encounter.scenes
    for scene_id, options, picked in (
        ("first_contact", scenes.first_contact.options, choices.first_contact),
        ("offering", scenes.offering.options, choices.offering),
        ("startle", scenes.startle.options, choices.startle),
    ):
        if picked not in {o.id for o in options}:
            raise InvalidAnswers(f"Unknown {scene_id} option {picked!r}")


async def complete_encounter(
    session: AsyncSession,
    data: GameData,
    calibration: matching.Calibration,
    user_id: UUID,
    attempt_id: UUID,
    choices: EncounterChoices,
) -> QuizAttemptDetail:
    """Match the player with the quiz answers plus encounter choices, and finish the attempt.

    Raises AttemptNotFound, AttemptConflict (already done, or the quiz has changed since)
    or InvalidAnswers (an unknown option).
    """
    row = await own_attempt(session, user_id, attempt_id, lock=True)
    if row.completed_at is not None:
        raise AttemptConflict("This attempt is already complete; a dragon has chosen you")
    if row.quiz_id != data.quiz.version:
        raise AttemptConflict(f"This attempt used {row.quiz_id}; take the quiz again")
    if choices.encounter_version != data.encounter.version:
        raise AttemptConflict(
            f"Encounter {choices.encounter_version} is no longer active; "
            f"reload to get {data.encounter.version}"
        )
    _check_choices(data, choices)

    result = matching.match(
        data,
        calibration,
        row.answers,
        matching.EncounterChoices(choices.first_contact, choices.offering, choices.startle),
    )
    row.encounter_signals = choices.model_dump()
    row.ranking = [
        {
            "species_id": m.species_id,
            "raw": round(m.score.raw, 6),
            "compatibility": m.compatibility,
            "explanation": m.explanation,
        }
        for m in (result.top, *result.runners_up)
    ]
    row.algorithm_version = result.algorithm_version
    row.completed_at = func.now()
    await session.commit()
    await session.refresh(row)
    return await _detail(session, data, row)
