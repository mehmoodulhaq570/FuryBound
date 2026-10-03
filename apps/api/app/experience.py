"""Additive gameplay using the existing event diary; no changes to player/chat tables.

Dragon row locks serialize mission choices and reward claims. The mission owns its
training session, so unrelated training results cannot be used to claim a rescue.
"""

from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DragonEventRow, PlayerDragonRow, TrainingSessionRow
from app.discoveries import discover
from app.dragons import NoDragon, Rulebook, mine, now, state
from app.engines import training
from app.schemas.experience import (
    Achievement,
    AdventureState,
    Experience,
    JournalEntry,
    Milestone,
)


class ExperienceConflict(ValueError):
    pass


async def _dragon(
    session: AsyncSession, user_id: UUID, dragon_id: UUID, *, lock: bool = False
) -> PlayerDragonRow:
    row = await mine(session, user_id, dragon_id, lock=lock)
    if row is None:
        raise NoDragon("This dragon isn't yours")
    return row


async def _events(session: AsyncSession, dragon_id: UUID) -> list[DragonEventRow]:
    return list(
        await session.scalars(
            select(DragonEventRow)
            .where(DragonEventRow.dragon_id == dragon_id)
            .order_by(DragonEventRow.created_at, DragonEventRow.id)
        )
    )


def achievements(events: list[DragonEventRow]) -> list[Achievement]:
    care_count = sum(e.kind in {"fed", "rested", "played"} for e in events)
    trained = [e for e in events if e.kind == "trained"]
    rescued = any(e.kind == "rescued" for e in events)
    best = max((int(e.payload.get("score", 0)) for e in trained), default=0)
    specs = [
        ("first_flight", "First wings", "Finish a training session", len(trained), 1, "lanterns"),
        (
            "care",
            "A place to belong",
            "Look after your dragon three times",
            care_count,
            3,
            "flowers",
        ),
        ("ace", "Clear skies", "Score 80 or more in training", best, 80, "pennant"),
        ("rescue", "A helping wing", "Complete the Misty Cove rescue", int(rescued), 1, "beacon"),
    ]
    return [
        Achievement(
            id=key,
            title=title,
            description=desc,
            earned=value >= target,
            progress=min(value, target),
            target=target,
            decoration=decoration,
        )
        for key, title, desc, value, target, decoration in specs
    ]


def next_milestone(book: Rulebook, row: PlayerDragonRow) -> Milestone | None:
    upcoming = [s for s in book.progression.stages if s.from_level > row.level]
    if not upcoming:
        return None
    stage = upcoming[0]
    activities = [a.label for a in book.progression.activities if a.stage == stage.id]
    remaining = (
        sum(
            training.xp_to_next(book.progression, level) or 0
            for level in range(row.level, stage.from_level)
        )
        - row.xp
    )
    label = f"{stage.label}: {', '.join(activities)}" if activities else stage.label
    return Milestone(label=label, level=stage.from_level, xp_remaining=max(0, remaining))


def _journal(event: DragonEventRow, name: str) -> str | None:
    p = event.payload
    match event.kind:
        case "adopted":
            return f"You and {name} began your story together."
        case "fed":
            return f"You shared {p.get('food', 'a meal')} with {name}."
        case "rested":
            return f"{name} settled down for a peaceful rest."
        case "played":
            return f"You made time to play with {name}."
        case "trained":
            return f"{name} practised {p.get('activity', 'training')}: {p.get('score', 0)}/100."
        case "level_up":
            return f"{name} reached level {p.get('level')}."
        case "rescued":
            return str(p.get("outcome", "You rescued a wild dragon at Misty Cove."))
        case _:
            return None


async def _adventure_state(session: AsyncSession, event: DragonEventRow) -> AdventureState:
    result = AdventureState.model_validate(event.payload)
    if result.training_session_id:
        sess = await session.get(TrainingSessionRow, result.training_session_id)
        if sess is not None:
            result.flight_finished = sess.completed_at is not None
            result.score = sess.score
    return result


async def overview(
    session: AsyncSession, book: Rulebook, user_id: UUID, dragon_id: UUID
) -> Experience:
    row = await _dragon(session, user_id, dragon_id)
    events = await _events(session, row.id)
    decorations = [e for e in events if e.kind == "habitat_decorated"]
    runs = [e for e in events if e.kind == "rescue_mission"]
    journal = [
        JournalEntry(id=e.id, text=text, at=e.created_at)
        for e in events
        if (text := _journal(e, row.name)) is not None
    ]
    return Experience(
        achievements=achievements(events),
        decoration=str(decorations[-1].payload["decoration"]) if decorations else "camp",
        milestone=next_milestone(book, row),
        journal=list(reversed(journal[-12:])),
        adventure=await _adventure_state(session, runs[-1]) if runs else None,
    )


async def decorate(session: AsyncSession, user_id: UUID, dragon_id: UUID, decoration: str) -> None:
    row = await _dragon(session, user_id, dragon_id, lock=True)
    badges = achievements(await _events(session, row.id))
    allowed = {"camp"} | {a.decoration for a in badges if a.earned}
    if decoration not in allowed:
        raise ExperienceConflict("Earn the matching achievement to unlock this decoration")
    session.add(
        DragonEventRow(
            dragon_id=row.id, kind="habitat_decorated", payload={"decoration": decoration}
        )
    )
    await session.commit()


async def start(session: AsyncSession, user_id: UUID, dragon_id: UUID) -> AdventureState:
    row = await _dragon(session, user_id, dragon_id, lock=True)
    runs = [e for e in await _events(session, row.id) if e.kind == "rescue_mission"]
    if runs:
        # Resume the same mission, including its already-earned result. Never farm rewards.
        return await _adventure_state(session, runs[-1])
    result = AdventureState(id=uuid4(), node="approach")
    session.add(
        DragonEventRow(
            dragon_id=row.id, kind="rescue_mission", payload=result.model_dump(mode="json")
        )
    )
    await session.commit()
    return result


async def choose(
    session: AsyncSession,
    book: Rulebook,
    user_id: UUID,
    dragon_id: UUID,
    run_id: UUID,
    choice: str,
) -> AdventureState:
    row = await _dragon(session, user_id, dragon_id, lock=True)
    events = await _events(session, row.id)
    event = next(
        (e for e in events if e.kind == "rescue_mission" and e.payload.get("id") == str(run_id)),
        None,
    )
    if event is None:
        raise NoDragon("No such rescue mission for this dragon")
    run = await _adventure_state(session, event)
    at = now()
    if run.node == "approach":
        if choice not in {"gentle", "bold", "clever"}:
            raise ExperienceConflict("Choose how to approach the cove first")
        activity = book.progression.activity("flight")
        needs, mood = await state(session, book, row, at)
        training.check_can_train(
            book.progression, activity, name=row.name, level=row.level, needs=needs
        )
        sess = TrainingSessionRow(
            dragon_id=row.id,
            activity="flight",
            mood=mood,
            needs_at_start={str(k): v for k, v in needs.items()},
            started_at=at,
        )
        session.add(sess)
        await session.flush()
        run.node, run.approach, run.training_session_id = "flight", choice, sess.id
    elif run.node == "flight":
        if choice != "continue" or run.training_session_id is None:
            raise ExperienceConflict("Complete the flight through the cove first")
        if not run.flight_finished:
            # A returning player can reopen an expired unfinished session safely.
            old_session = await session.get(TrainingSessionRow, run.training_session_id)
            if old_session and at - old_session.started_at > timedelta(
                minutes=book.progression.session_expires_minutes
            ):
                needs, mood = await state(session, book, row, at)
                training.check_can_train(
                    book.progression,
                    book.progression.activity("flight"),
                    name=row.name,
                    level=row.level,
                    needs=needs,
                )
                replacement = TrainingSessionRow(
                    dragon_id=row.id,
                    activity="flight",
                    mood=mood,
                    needs_at_start={str(k): v for k, v in needs.items()},
                    started_at=at,
                )
                session.add(replacement)
                await session.flush()
                run.training_session_id = replacement.id
                event.payload = run.model_dump(mode="json")
                await session.commit()
                return run
            # 'continue' also prepares an unfinished flight after returning to the mission.
            return run
        run.node = "rescue"
    elif run.node == "rescue":
        if choice not in {"untie", "lift"}:
            raise ExperienceConflict("Choose how to free the trapped dragon")
        trait = {"gentle": "patience", "bold": "courage", "clever": "intelligence"}[
            run.approach or "gentle"
        ]
        affinity = row.personality.get(trait, 50)
        skill = row.stats.get("strength" if choice == "lift" else "intelligence", 30)
        strong = affinity >= 55 or skill >= 40 or (run.score or 0) >= 70
        method = "lifted the net together" if choice == "lift" else "patiently loosened the knots"
        run.outcome = f"You and {row.name} {method}. The Scuttleclaw {
            'bounded free and nudged your hand'
            if strong
            else 'needed a little extra time, then fluttered safely back to shore'
        }."
        run.xp_reward, run.trust_reward = (80 if strong else 60), (5 if strong else 3)
        row.xp += run.xp_reward
        while (
            need := training.xp_to_next(book.progression, row.level)
        ) is not None and row.xp >= need:
            row.xp -= need
            row.level += 1
            session.add(
                DragonEventRow(dragon_id=row.id, kind="level_up", payload={"level": row.level})
            )
        row.stage = training.stage_for(book.progression, row.level).id
        row.trust = min(100, row.trust + run.trust_reward)
        run.node, run.discovered_species = "complete", "scuttleclaw"
        await discover(session, user_id, ["scuttleclaw"], "story")
        session.add(
            DragonEventRow(dragon_id=row.id, kind="rescued", payload=run.model_dump(mode="json"))
        )
    else:
        raise ExperienceConflict("This rescue is already complete; its rewards are saved")
    event.payload = run.model_dump(mode="json")
    await session.commit()
    return run
