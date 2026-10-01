"""Monte Carlo calibration of the matching engine (Plan.md §9.3).

Simulates players who answer the quiz and the encounter at random, then:
- reports how often each species is the top match, against the Plan's targets;
- writes data/build/matching_calibration.json, whose quantiles turn a raw match score into
  the displayed 60-99% compatibility.

Targets: no species above 20%; legendary species between 0.5% and 3% (reachable but rare);
every other species at least 3%.

Run from the repo root:   pnpm match:calibrate
CI runs it with --check:  fails if the targets are missed or the saved file is out of date.
"""

import argparse
import json
import random
import sys
from collections import Counter

from app.engines.game_data import TRAITS, GameData, load_game_data
from app.engines.matching import (
    ALGORITHM_VERSION,
    CALIBRATION_PATH,
    EncounterChoices,
    fingerprint,
    match_vector,
    rank_species,
    raw_totals,
)

SEED = 20261001
RUNS = 100_000
MAX_SHARE, MIN_SHARE = 20.0, 3.0
LEGENDARY_MIN, LEGENDARY_MAX = 0.5, 3.0


def simulate(data: GameData, runs: int, seed: int) -> tuple[Counter[str], list[float]]:
    rng = random.Random(seed)
    scenes = data.encounter.scenes
    tops: Counter[str] = Counter()
    best: list[float] = []
    for _ in range(runs):
        answers = {q.id: rng.choice(q.options).id for q in data.quiz.questions}
        choices = EncounterChoices(
            first_contact=rng.choice(scenes.first_contact.options).id,
            offering=rng.choice(scenes.offering.options).id,
            startle=rng.choice(scenes.startle.options).id,
        )
        player = match_vector(data, raw_totals(data.quiz, answers), choices.startle)
        winner = rank_species(data, player, choices)[0]
        tops[winner.species_id] += 1
        best.append(winner.raw)
    return tops, best


def check_targets(data: GameData, shares: dict[str, float]) -> list[str]:
    problems = []
    for s in data.species:
        share = shares[s.id]
        if s.rarity == "legendary":
            if not LEGENDARY_MIN <= share <= LEGENDARY_MAX:
                problems.append(
                    f"{s.id} (legendary) is {share:.2f}%; target {LEGENDARY_MIN}-{LEGENDARY_MAX}%"
                )
        elif share < MIN_SHARE:
            problems.append(f"{s.id} is {share:.2f}%; target at least {MIN_SHARE}%")
        if share > MAX_SHARE:
            problems.append(f"{s.id} is {share:.2f}%; target at most {MAX_SHARE}%")
    return problems


def quantiles(values: list[float], points: int = 101) -> list[float]:
    ordered = sorted(values)
    last = len(ordered) - 1
    return [round(ordered[round(i * last / (points - 1))], 6) for i in range(points)]


def report(data: GameData, shares: dict[str, float], runs: int) -> None:
    print(
        f"Top-match share over {runs:,} random players ({ALGORITHM_VERSION}, {data.quiz.version})"
    )
    print(f"{'species':22} {'rarity':10} {'share':>7}")
    for s in sorted(data.species, key=lambda s: -shares[s.id]):
        bar = "#" * round(shares[s.id] * 2)
        print(f"{s.id:22} {s.rarity:10} {shares[s.id]:6.2f}%  {bar}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--check", action="store_true", help="don't write; fail if out of date")
    args = parser.parse_args()

    data = load_game_data()
    assert set(TRAITS) == {t.id for t in data.traits.traits}
    tops, best = simulate(data, args.runs, args.seed)
    shares = {s.id: round(100 * tops[s.id] / args.runs, 2) for s in data.species}
    report(data, shares, args.runs)

    problems = check_targets(data, shares)
    for p in problems:
        print(f"TARGET MISSED: {p}")

    output = {
        "algorithm_version": ALGORITHM_VERSION,
        "quiz_version": data.quiz.version,
        "fingerprint": fingerprint(data),
        "runs": args.runs,
        "seed": args.seed,
        "targets_met": not problems,
        "top_match_share": shares,
        "best_raw_quantiles": quantiles(best),
    }
    text = json.dumps(output, indent=2) + "\n"

    if args.check:
        current = CALIBRATION_PATH.read_text(encoding="utf-8") if CALIBRATION_PATH.exists() else ""
        if current != text:
            print("matching_calibration.json is out of date: run `pnpm match:calibrate`")
            return 1
        return 1 if problems else 0
    if args.runs != RUNS or args.seed != SEED:
        print("Trial run (non-default --runs/--seed): nothing written.")
        return 1 if problems else 0
    CALIBRATION_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {CALIBRATION_PATH}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
