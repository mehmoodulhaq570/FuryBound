"""Matching engine and game data (Plan.md §9.2-9.4). No database needed."""

import csv
import json
from pathlib import Path

import pytest

from app.engines.game_data import TRAITS, GameData, load_game_data
from app.engines.matching import (
    CALIBRATION_PATH,
    Calibration,
    EncounterChoices,
    compatibility,
    display_scores,
    encounter_bonus,
    load_calibration,
    match,
    match_vector,
    rank_species,
    raw_totals,
)

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def data() -> GameData:
    return load_game_data()


@pytest.fixture(scope="module")
def calibration(data: GameData) -> Calibration:
    return load_calibration(data)


def answers_from(data: GameData, letters: str) -> dict[str, str]:
    """'b c c b …' -> {question id: option id}, in quiz order."""
    picks = letters.split()
    assert len(picks) == len(data.quiz.questions)
    return {q.id: pick for q, pick in zip(data.quiz.questions, picks, strict=True)}


# ── game data ────────────────────────────────────────────────────────────────


def test_profiles_reference_real_species_and_skip_titans(data: GameData) -> None:
    with (ROOT / "data" / "catalog" / "species.csv").open(encoding="utf-8") as fh:
        catalog = {row["species_id"] for row in csv.DictReader(fh)}
    ids = {s.id for s in data.species}
    assert ids <= catalog
    assert not ids & {"red_death", "bewilderbeast"}
    assert {s.id for s in data.species if s.rarity == "legendary"} == {"night_fury", "light_fury"}


def test_every_trait_can_reach_both_ends(data: GameData) -> None:
    for trait in TRAITS:
        low, high = data.quiz.bounds(trait)
        assert low < 0 < high


# ── quiz scoring ─────────────────────────────────────────────────────────────


def test_unanswered_question_is_rejected(data: GameData) -> None:
    answers = answers_from(data, " ".join("a" * len(data.quiz.questions)))
    answers.pop(data.quiz.questions[0].id)
    with pytest.raises(ValueError, match="missing"):
        raw_totals(data.quiz, answers)


def test_scores_stay_within_0_and_100(data: GameData) -> None:
    for letter in "abcd":
        totals = raw_totals(data.quiz, answers_from(data, " ".join(letter * 12)))
        assert all(0 <= v <= 100 for v in display_scores(data.quiz, totals).values())
        assert all(0 <= v <= 100 for v in match_vector(data, totals).values())


def test_percentiles_rise_with_the_raw_total(data: GameData) -> None:
    low = match_vector(
        data, raw_totals(data.quiz, answers_from(data, ARCHETYPES["calm_homebody"][0]))
    )
    high = match_vector(
        data, raw_totals(data.quiz, answers_from(data, ARCHETYPES["reckless_daredevil"][0]))
    )
    assert high["courage"] > low["courage"]
    assert high["patience"] < low["patience"]


# ── encounter ────────────────────────────────────────────────────────────────


def test_encounter_bonus_extremes(data: GameData) -> None:
    gronckle = next(s for s in data.species if s.id == "gronckle")  # gentle, likes rock
    best = EncounterChoices(first_contact="speak_softly", offering="rock")
    worst = EncounterChoices(first_contact="reach_out")  # bold is the opposite of gentle
    assert encounter_bonus(data, best, gronckle) == 1.0
    assert encounter_bonus(data, worst, gronckle) == 0.25
    assert encounter_bonus(data, EncounterChoices(), gronckle) == 0.5


def test_unknown_encounter_option_is_rejected(data: GameData) -> None:
    gronckle = next(s for s in data.species if s.id == "gronckle")
    with pytest.raises(KeyError):
        encounter_bonus(data, EncounterChoices(offering="cake"), gronckle)


# ── archetype fixtures: expected top-3 (Plan §9.3) ───────────────────────────

# name: (answers to q01…q12, must be in the top 3, must not be in the top 3)
ARCHETYPES: dict[str, tuple[str, set[str], set[str]]] = {
    "cautious_scholar": (
        "b c c b d b b d c c c a",
        {"stormcutter"},
        {"deathgripper", "monstrous_nightmare", "scuttleclaw"},
    ),
    "reckless_daredevil": (
        "a a d c c a d a a d d b",
        {"deathgripper"},
        {"gronckle", "hotburple", "stormcutter"},
    ),
    "loyal_friend": (
        "d b b a b c a c d a a c",
        {"gronckle"},
        {"deathgripper", "light_fury", "crimson_goregutter"},
    ),
    "lone_wolf": (
        "c d a c a d d d b b a b",
        {"crimson_goregutter"},
        {"gronckle", "hobgobbler"},
    ),
    "curious_explorer": (
        "c c d d a b b a b b d b",
        {"scuttleclaw"},
        {"gronckle", "hotburple"},
    ),
    "calm_homebody": (
        "b b c b b c a b c a c a",
        {"gronckle", "hotburple"},
        {"deathgripper", "monstrous_nightmare", "scuttleclaw"},
    ),
}


@pytest.mark.parametrize("name", ARCHETYPES)
def test_archetype_top_three(data: GameData, name: str) -> None:
    letters, expected, excluded = ARCHETYPES[name]
    player = match_vector(data, raw_totals(data.quiz, answers_from(data, letters)))
    top3 = {s.species_id for s in rank_species(data, player, EncounterChoices())[:3]}
    assert expected <= top3, f"{name}: top 3 was {top3}"
    assert not excluded & top3, f"{name}: top 3 was {top3}"


# ── full result and calibration ──────────────────────────────────────────────


def test_match_result_is_complete_and_deterministic(
    data: GameData, calibration: Calibration
) -> None:
    answers = answers_from(data, ARCHETYPES["curious_explorer"][0])
    choices = EncounterChoices("toss_pebble", "fish", "laugh_it_off")
    result = match(data, calibration, answers, choices)
    assert result == match(data, calibration, answers, choices)
    assert result.top.species_id == "scuttleclaw"
    assert len(result.runners_up) == 2
    shown = [result.top, *result.runners_up]
    assert all(60 <= m.compatibility <= 99 for m in shown)
    assert [m.score.raw for m in shown] == sorted((m.score.raw for m in shown), reverse=True)
    assert all(m.explanation.endswith(".") and m.explanation[0].isupper() for m in shown)
    assert "curiosity" in result.top.explanation


def test_compatibility_maps_onto_60_to_99(calibration: Calibration) -> None:
    q = calibration.best_raw_quantiles
    assert compatibility(q[0] - 1, calibration) == 60
    assert compatibility(q[-1] + 1, calibration) == 99
    assert compatibility(q[50], calibration) in range(78, 81)


def test_saved_calibration_meets_the_targets() -> None:
    saved = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    assert saved["targets_met"] is True
    assert len(saved["best_raw_quantiles"]) == 101
