"""Training sessions: start, finish once, history (Plan.md §9.6)."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DragonEventRow, PlayerDragonRow, TrainingSessionRow
from app.dragons import NoDragon, Rulebook, mine, now, present, state
from app.engines import training
from app.schemas.training import (
    ActivityResult,
    HistoryEntry,
    StageInfo,
    StatChange,
    TrainingActivity,
    TrainingOverview,
    TrainingResult,
    TrainingSession,
)


class UnknownActivity(ValueError):
    pass


class SessionNotFound(LookupError):
    pass


class SessionClosed(ValueError):
    """Already completed, or started too long ago."""


def _stage(stage: training.Stage) -> StageInfo:
    return StageInfo(id=stage.id, label=stage.label)


async def _dragon(
    session: AsyncSession, user_id: UUID, dragon_id: UUID, *, lock: bool = False
) -> PlayerDragonRow:
    row = await mine(session, user_id, dragon_id, lock=lock)
    if row is None:
        raise NoDragon(f"No dragon {dragon_id}")
    return row


async def overview(
    session: AsyncSession, book: Rulebook, user_id: UUID, dragon_id: UUID
) -> TrainingOverview:
    rules = book.progression
    row = await _dragon(session, user_id, dragon_id)
    open_ids = {a.id for a in training.unlocked(rules, row.level)}
    return TrainingOverview(
        level=row.level,
        xp=row.xp,
        xp_to_next=training.xp_to_next(rules, row.level),
        stage=_stage(training.stage_for(rules, row.level)),
        activities=[
            TrainingActivity(
                id=a.id,
                label=a.label,
                description=a.description,
                trains=list(a.trains),
                energy_cost=a.energy_cost,
                unlocked=a.id in open_ids,
                unlocks_at=_stage(rules.stage(a.stage)),
                unlocks_at_level=rules.stage(a.stage).from_level,
            )
            for a in rules.activities
        ],
    )


async def start(
    session: AsyncSession, book: Rulebook, user_id: UUID, dragon_id: UUID, activity_id: str
) -> TrainingSession:
    """Open a session. Raises NoDragon, UnknownActivity, training.Locked or training.Refused.

    A refusal is logged as an event: a low-trust dragon that refused recently is Angry.
    """
    rules = book.progression
    try:
        activity = rules.activity(activity_id)
    except KeyError as exc:
        raise UnknownActivity(f"Unknown activity {activity_id!r}") from exc
    row = await _dragon(session, user_id, dragon_id)
    at = now()
    needs, mood = await state(session, book, row, at)
    try:
        training.check_can_train(rules, activity, name=row.name, level=row.level, needs=needs)
    except training.Refused as exc:
        session.add(
            DragonEventRow(
                dragon_id=row.id, kind="refused", payload={"activity": activity.id, "why": str(exc)}
            )
        )
        await session.commit()
        raise

    session_row = TrainingSessionRow(
        dragon_id=row.id,
        activity=activity.id,
        mood=mood,
        needs_at_start={str(n): v for n, v in needs.items()},
        started_at=at,
    )
    session.add(session_row)
    await session.commit()
    return TrainingSession(
        id=session_row.id,
        activity=activity.id,
        started_at=at,
        min_ms=activity.min_ms,
        max_ms=activity.max_ms,
    )


async def finish(
    session: AsyncSession, book: Rulebook, user_id: UUID, session_id: UUID, result: ActivityResult
) -> TrainingResult:
    """Score a session, once. Raises SessionNotFound, SessionClosed or training.Implausible."""
    rules = book.progression
    query = (
        select(TrainingSessionRow, PlayerDragonRow)
        .join(PlayerDragonRow, PlayerDragonRow.id == TrainingSessionRow.dragon_id)
        .where(TrainingSessionRow.id == session_id, PlayerDragonRow.user_id == user_id)
        .with_for_update()
    )
    found = (await session.execute(query)).one_or_none()
    if found is None:
        raise SessionNotFound(f"No training session {session_id}")
    sess, row = found

    at = now()
    if sess.completed_at is not None:
        raise SessionClosed("This session is already finished")
    if at - sess.started_at > timedelta(minutes=rules.session_expires_minutes):
        raise SessionClosed("This session has expired; start a new one")
    activity = rules.activity(sess.activity)
    training.check_duration(
        activity, result.duration_ms, (at - sess.started_at).total_seconds() * 1000
    )

    needs, _ = await state(session, book, row, at)
    caps = next(s for s in book.game.species if s.id == row.species_id).stat_caps
    outcome = training.complete(
        rules,
        activity,
        name=row.name,
        score=result.score,
        mood=sess.mood,  # type: ignore[arg-type]  # stored from care.Mood
        needs_at_start=sess.needs_at_start,  # type: ignore[arg-type]
        needs=needs,
        trust=row.trust,
        stats=row.stats,  # type: ignore[arg-type]
        caps=caps,
        level=row.level,
        xp=row.xp,
    )

    row.stats = {str(k): v for k, v in outcome.stats.items()}
    row.level, row.xp, row.stage = outcome.level, outcome.xp, outcome.stage.id
    row.needs = {str(k): v for k, v in outcome.needs.items()}
    row.needs_updated_at = at
    row.trust = outcome.trust
    sess.completed_at = at
    sess.score = result.score
    sess.duration_ms = result.duration_ms
    sess.xp_gained = outcome.xp_gained
    sess.stat_deltas = {str(k): v for k, v in outcome.stat_deltas.items()}
    sess.stats_after = row.stats
    sess.client_meta = result.meta
    payload = {"activity": activity.id, "score": result.score, "xp": outcome.xp_gained}
    session.add(DragonEventRow(dragon_id=row.id, kind="trained", payload=payload))
    for level in outcome.level_ups:
        session.add(DragonEventRow(dragon_id=row.id, kind="level_up", payload={"level": level}))
    await session.commit()
    await session.refresh(row)

    return TrainingResult(
        message=outcome.message,
        score=result.score,
        xp_gained=outcome.xp_gained,
        stat_changes=[
            StatChange(id=s, label=s.title(), delta=d, value=outcome.stats[s])
            for s, d in outcome.stat_deltas.items()
        ],
        level_ups=list(outcome.level_ups),
        stage=_stage(outcome.stage),
        new_activities=list(outcome.new_activities),
        dragon=await present(session, book, row, at),
    )


async def history(session: AsyncSession, user_id: UUID, dragon_id: UUID) -> list[HistoryEntry]:
    """Finished sessions, oldest first: what was trained and the stats afterwards."""
    await _dragon(session, user_id, dragon_id)
    rows = await session.scalars(
        select(TrainingSessionRow)
        .where(
            TrainingSessionRow.dragon_id == dragon_id,
            TrainingSessionRow.completed_at.is_not(None),
        )
        .order_by(TrainingSessionRow.completed_at)
    )
    return [
        HistoryEntry(
            id=r.id,
            activity=r.activity,
            completed_at=r.completed_at,
            score=r.score or 0,
            xp_gained=r.xp_gained or 0,
            stat_deltas=r.stat_deltas or {},
            stats_after=r.stats_after or {},
        )
        for r in rows
    ]
