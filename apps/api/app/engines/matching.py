"""Quiz scoring and dragon matching (Plan.md §9.2-9.4). Pure: no I/O besides loading files,
no randomness, so the same answers always give the same dragon.

One deliberate change from the Plan: before comparing with dragons, the player's raw quiz
totals are converted to percentiles ("higher than 80% of players" -> 80). Summing twelve mixed
answers makes most players land in the middle, while dragons have strong personalities;
compared directly, the bold dragons could never win. The Plan's min-max scores are still
computed, for display.

Percentiles assume every answer is equally likely, which can be calculated exactly. Once real
attempts exist (Plan §9.3, ML extensions) they can be swapped for the observed distribution.
"""

import bisect
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.engines.game_data import (
    TRAITS,
    GameData,
    Quiz,
    SpeciesProfile,
    Trait,
    get_game_data,
)

ALGORITHM_VERSION = "match_v1"
CALIBRATION_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "build" / "matching_calibration.json"
)

# raw = 0.70*S + 0.15*C + 0.15*B - P   (Plan §9.3 step 5)
W_SIMILARITY, W_COMPLEMENT, W_ENCOUNTER = 0.70, 0.15, 0.15
MAX_PENALTY = 0.3
COMPAT_FLOOR, COMPAT_SPAN = 60, 39  # displayed compatibility 60-99%

TraitVector = dict[Trait, float]


# ── quiz scoring ─────────────────────────────────────────────────────────────


def raw_totals(quiz: Quiz, answers: Mapping[str, str]) -> dict[Trait, int]:
    """Sum the trait deltas of the chosen options. Every question must be answered once."""
    expected = {q.id for q in quiz.questions}
    if set(answers) != expected:
        missing, extra = expected - set(answers), set(answers) - expected
        raise ValueError(f"answers don't match {quiz.version}: missing={missing}, extra={extra}")
    totals = dict.fromkeys(TRAITS, 0)
    for question in quiz.questions:
        for trait, delta in question.option(answers[question.id]).deltas.items():
            totals[trait] += delta
    return totals


def display_scores(quiz: Quiz, totals: Mapping[Trait, int]) -> TraitVector:
    """The Plan's 0-100 trait scores: min-max scaled within what the quiz allows."""
    scores: TraitVector = {}
    for trait in TRAITS:
        low, high = quiz.bounds(trait)
        scores[trait] = 100 * (totals[trait] - low) / (high - low)
    return scores


_TABLES: dict[int, tuple[Quiz, dict[Trait, dict[int, float]]]] = {}


def _percentile_table(quiz: Quiz, trait: Trait) -> dict[int, float]:
    cached = _TABLES.get(id(quiz))
    if cached is None or cached[0] is not quiz:
        cached = _TABLES[id(quiz)] = (quiz, {t: _exact_percentiles(quiz, t) for t in TRAITS})
    return cached[1][trait]


def _exact_percentiles(quiz: Quiz, trait: Trait) -> dict[int, float]:
    """Exact mid-rank percentile (0-1) of every reachable raw total, if answers were random."""
    dist = {0: 1.0}
    for question in quiz.questions:
        step: dict[int, float] = {}
        share = 1 / len(question.options)
        for total, p in dist.items():
            for opt in question.options:
                key = total + opt.deltas.get(trait, 0)
                step[key] = step.get(key, 0.0) + p * share
        dist = step
    table, below = {}, 0.0
    for total in sorted(dist):
        table[total] = below + dist[total] / 2
        below += dist[total]
    return table


def match_vector(
    data: GameData, totals: Mapping[Trait, int], startle: str | None = None
) -> TraitVector:
    """Player traits on the dragons' scale: percentile x 100, plus the startle-scene nudge."""
    nudges: Mapping[Trait, int] = {}
    if startle is not None:
        nudges = _by_id(data.encounter.scenes.startle.options, startle).deltas
    weight = data.encounter.startle_weight
    vector: TraitVector = {}
    for trait in TRAITS:
        value = 100 * _percentile_table(data.quiz, trait)[totals[trait]]
        vector[trait] = _clamp(value + weight * nudges.get(trait, 0))
    return vector


# ── matching ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EncounterChoices:
    """Option ids picked in the three encounter scenes (Plan §9.4); None = skipped."""

    first_contact: str | None = None
    offering: str | None = None
    startle: str | None = None


@dataclass(frozen=True)
class SpeciesScore:
    species_id: str
    raw: float
    similarity: float
    complement: float
    encounter: float
    penalty: float
    fired_rules: tuple[str, ...]


def similarity(player: TraitVector, dragon: SpeciesProfile) -> float:
    """S = 1 - sqrt(sum w (U - D)^2 / sum w) / 100, in 0-1."""
    weights = [dragon.weight(t) for t in TRAITS]
    sq = sum(w * (player[t] - dragon.traits[t]) ** 2 for w, t in zip(weights, TRAITS, strict=True))
    return 1 - math.sqrt(sq / sum(weights)) / 100


def complement(
    data: GameData, player: TraitVector, dragon: SpeciesProfile
) -> tuple[float, tuple[str, ...]]:
    """C = mean of the rewarded trainer traits over the rules that fire, else 0.5."""
    fired = [r for r in data.complements.rules if r.when.fires(dragon)]
    if not fired:
        return 0.5, ()
    value = sum(player[r.reward.trainer] for r in fired) / len(fired) / 100
    return value, tuple(r.id for r in fired)


def penalty(player: TraitVector, dragon: SpeciesProfile) -> float:
    """P = min(0.3, sum max(0, min_t - U_t) / 100 x 0.5)."""
    shortfall = sum(max(0.0, need - player[t]) for t, need in dragon.requirements.items())
    return min(MAX_PENALTY, shortfall / 100 * 0.5)


def encounter_bonus(data: GameData, choices: EncounterChoices, dragon: SpeciesProfile) -> float:
    """B = 0.5 + 0.25 * approach_match + 0.25 * diet_match, each match in {-1, 0, +1}."""
    approach_match = 0
    if choices.first_contact is not None:
        approach = _by_id(
            data.encounter.scenes.first_contact.options, choices.first_contact
        ).approach
        if approach == dragon.approach_pref:
            approach_match = 1
        elif data.encounter.approach_opposites.get(approach) == dragon.approach_pref:
            approach_match = -1
    diet_match = 0
    if choices.offering is not None:
        food = _by_id(data.encounter.scenes.offering.options, choices.offering).food
        diet_match = 1 if food in dragon.diet_likes else -1 if food in dragon.diet_dislikes else 0
    return 0.5 + 0.25 * approach_match + 0.25 * diet_match


def score_species(
    data: GameData, player: TraitVector, choices: EncounterChoices, dragon: SpeciesProfile
) -> SpeciesScore:
    s = similarity(player, dragon)
    c, fired = complement(data, player, dragon)
    b = encounter_bonus(data, choices, dragon)
    p = penalty(player, dragon)
    raw = W_SIMILARITY * s + W_COMPLEMENT * c + W_ENCOUNTER * b - p
    return SpeciesScore(dragon.id, raw, s, c, b, p, fired)


def rank_species(
    data: GameData, player: TraitVector, choices: EncounterChoices
) -> list[SpeciesScore]:
    """All matchable species, best first; ties go to the alphabetically first id."""
    scores = [score_species(data, player, choices, d) for d in data.species]
    return sorted(scores, key=lambda s: (-s.raw, s.species_id))


# ── displayed result ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Calibration:
    """Output of scripts/calibrate_matching.py (data/build/matching_calibration.json)."""

    fingerprint: str
    best_raw_quantiles: tuple[float, ...]  # 101 points: 0th, 1st, … 100th percentile


@dataclass(frozen=True)
class SpeciesMatch:
    species_id: str
    compatibility: int  # 60-99
    explanation: str
    score: SpeciesScore


@dataclass(frozen=True)
class MatchResult:
    algorithm_version: str
    quiz_version: str
    traits: TraitVector  # min-max 0-100, for display
    top: SpeciesMatch
    runners_up: tuple[SpeciesMatch, ...]


def fingerprint(data: GameData) -> str:
    """Identifies the exact inputs a calibration was made from (ignores whitespace and comments)."""
    payload = json.dumps(
        {"algorithm": ALGORITHM_VERSION, "data": data.model_dump(mode="json")}, sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def load_calibration(data: GameData, path: Path = CALIBRATION_PATH) -> Calibration:
    raw = json.loads(path.read_text(encoding="utf-8"))
    calibration = Calibration(raw["fingerprint"], tuple(raw["best_raw_quantiles"]))
    if calibration.fingerprint != fingerprint(data):
        raise RuntimeError(
            "matching_calibration.json is out of date with data/game; run `pnpm match:calibrate`"
        )
    return calibration


@lru_cache
def get_calibration() -> Calibration:
    """The calibration for the loaded game data (raises if it is stale)."""
    return load_calibration(get_game_data())


def compatibility(raw: float, calibration: Calibration) -> int:
    """60 + 39 x percentile of raw among the simulated best-match scores."""
    q = calibration.best_raw_quantiles
    if raw <= q[0]:
        pct = 0.0
    elif raw >= q[-1]:
        pct = 1.0
    else:
        i = bisect.bisect_right(q, raw)
        lo, hi = q[i - 1], q[i]
        pct = (i - 1 + (raw - lo) / (hi - lo if hi > lo else 1)) / (len(q) - 1)
    return round(COMPAT_FLOOR + COMPAT_SPAN * pct)


def explain(
    data: GameData, player: TraitVector, dragon: SpeciesProfile, fired: Sequence[str]
) -> str:
    """Up to three reasons: shared strong traits, then complement rules the player satisfies."""
    labels = {t.id: t.label.lower() for t in data.traits.traits}
    shared = sorted(
        (
            t
            for t in TRAITS
            if dragon.traits[t] >= 60
            and player[t] >= 55
            and abs(player[t] - dragon.traits[t]) <= 25
        ),
        key=lambda t: (-dragon.weight(t) * (1 - abs(player[t] - dragon.traits[t]) / 100), t),
    )[:2]
    rules = {r.id: r for r in data.complements.rules}
    balancing = sorted(
        (rules[r] for r in fired if player[rules[r].reward.trainer] >= 60),
        key=lambda r: -player[r.reward.trainer],
    )[: 3 - len(shared)]

    clauses = []
    if shared:
        names = " and ".join(labels[t] for t in shared)
        clauses.append(
            f"your high {names} closely match{'es' if len(shared) == 1 else ''} this dragon's"
        )
    clauses += [r.reason for r in balancing]
    if not clauses:
        closest = min(
            TRAITS, key=lambda t: (abs(player[t] - dragon.traits[t]) / dragon.weight(t), t)
        )
        clauses.append(f"your {labels[closest]} is a close fit for this dragon's")
    text = "; ".join(clauses)
    return text[0].upper() + text[1:] + "."


def match(
    data: GameData,
    calibration: Calibration,
    answers: Mapping[str, str],
    choices: EncounterChoices | None = None,
    runners_up: int = 2,
) -> MatchResult:
    choices = choices or EncounterChoices()
    totals = raw_totals(data.quiz, answers)
    player = match_vector(data, totals, choices.startle)
    ranked = rank_species(data, player, choices)
    by_id = {s.id: s for s in data.species}

    def present(score: SpeciesScore) -> SpeciesMatch:
        dragon = by_id[score.species_id]
        return SpeciesMatch(
            species_id=score.species_id,
            compatibility=compatibility(score.raw, calibration),
            explanation=explain(data, player, dragon, score.fired_rules),
            score=score,
        )

    return MatchResult(
        algorithm_version=ALGORITHM_VERSION,
        quiz_version=data.quiz.version,
        traits=display_scores(data.quiz, totals),
        top=present(ranked[0]),
        runners_up=tuple(present(s) for s in ranked[1 : 1 + runners_up]),
    )


def _by_id[T](options: Sequence[T], option_id: str) -> T:
    for opt in options:
        if getattr(opt, "id", None) == option_id:
            return opt
    raise KeyError(f"no encounter option {option_id!r}")


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))
