"""Structured memory (Plan.md §9.9, tier 1): what a dragon "knows" from its own diary.

Pure and deterministic: no AI. It reads `dragon_events` (fed, trained, refused, played, ...)
and sums them up: favourite food and activity, dislikes, how much you've done together.
The chat prompt and the Dragon's Journal both use it. It's cheap, so it's worked out when
needed rather than stored.
"""

from collections import Counter, defaultdict
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class Event:
    kind: str
    payload: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class MemorySummary:
    favourite_food: str | None
    favourite_activity: str | None
    disliked_foods: tuple[str, ...]  # foods it was given and doesn't like
    refused_activities: tuple[str, ...]
    times_fed: int
    times_played: int
    sessions_trained: int
    days_together: int
    streak_days: int  # consecutive days, up to today, with any care or training

    def lines(self) -> list[str]:
        """Plain sentences for the prompt and the journal (only what's actually known)."""
        out = []
        if self.favourite_food:
            out.append(f"Favourite food so far: {self.favourite_food}.")
        if self.disliked_foods:
            out.append(f"Has been given foods it dislikes: {', '.join(self.disliked_foods)}.")
        if self.favourite_activity:
            out.append(f"Best training activity: {self.favourite_activity}.")
        if self.refused_activities:
            out.append(f"Has refused to train at: {', '.join(self.refused_activities)}.")
        out.append(
            f"Together for {self.days_together} day{'s' * (self.days_together != 1)}: "
            f"fed {self.times_fed} times, played {self.times_played} times, "
            f"trained {self.sessions_trained} times."
        )
        if self.streak_days > 1:
            out.append(f"Looked after every day for {self.streak_days} days in a row.")
        return out


CARE_KINDS = frozenset({"fed", "rested", "played", "trained", "chatted"})


def summarize(
    events: Sequence[Event],
    *,
    likes: Collection[str],
    dislikes: Collection[str],
    today: date,
) -> MemorySummary:
    fed = Counter(e.payload["food"] for e in events if e.kind == "fed" and "food" in e.payload)
    # The most-fed food it likes; otherwise the most-fed one it doesn't mind.
    liked_fed = [f for f, _ in fed.most_common() if f in likes]
    neutral_fed = [f for f, _ in fed.most_common() if f not in dislikes]
    favourite_food = (liked_fed or neutral_fed or [None])[0]

    scores: dict[str, list[int]] = defaultdict(list)
    for e in events:
        if e.kind == "trained" and "activity" in e.payload:
            scores[e.payload["activity"]].append(int(e.payload.get("score", 0)))
    favourite_activity = max(
        scores, key=lambda a: (sum(scores[a]) / len(scores[a]), a), default=None
    )

    adopted = min((e.created_at.date() for e in events if e.kind == "adopted"), default=today)
    active_days = {e.created_at.date() for e in events if e.kind in CARE_KINDS}
    streak, day = 0, today
    if day not in active_days:  # a streak can still be alive if today hasn't started yet
        day -= timedelta(days=1)
    while day in active_days:
        streak += 1
        day -= timedelta(days=1)

    return MemorySummary(
        favourite_food=favourite_food,
        favourite_activity=favourite_activity,
        disliked_foods=tuple(sorted(f for f in fed if f in dislikes)),
        refused_activities=tuple(
            sorted(
                {
                    e.payload["activity"]
                    for e in events
                    if e.kind == "refused" and "activity" in e.payload
                }
            )
        ),
        times_fed=sum(fed.values()),
        times_played=sum(e.kind == "played" for e in events),
        sessions_trained=sum(e.kind == "trained" for e in events),
        days_together=(today - adopted).days + 1,
        streak_days=streak,
    )
