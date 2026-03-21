from __future__ import annotations

import random

import pytest

from app.models.schemas import (
    BuildingState,
    ReputationState,
    SaveState,
    StudentState,
)
from app.services.events import (
    EVENTS,
    EventDefinition,
    apply_event,
    compute_education_power,
    pick_event,
)


def _make_save(**overrides) -> SaveState:
    """Build a SaveState suitable for testing using model_validate."""
    data = {
        "userId": "test_user",
        "year": 1,
        "month": 1,
        "budget": 500,
        "reputation": {"arts": 10, "engineering": 10, "medical": 10, "humanities": 10},
        "students": {"enrolled": 50, "averageLevel": 5.0},
        "admissionPolicy": "normal",
        "buildings": {"classroom": 2, "dormitory": 1, "laboratory": 1, "cafeteria": 1},
        "departments": ["humanities", "art"],
        "logs": [],
        "admissionCriteria": {"math": 5, "science": 5, "english": 5, "korean": 5},
    }
    data.update(overrides)
    return SaveState.model_validate(data)


# ---------------------------------------------------------------------------
# compute_education_power
# ---------------------------------------------------------------------------

def test_compute_education_power():
    # classroom=2 → 2*8=16, cafeteria=1 → 1*2=2
    # departments=['humanities','art']: humanities education_boost=4, art=4 → 8
    # total = 16 + 2 + 8 = 26
    save = _make_save()
    assert compute_education_power(save) == 26


# ---------------------------------------------------------------------------
# pick_event
# ---------------------------------------------------------------------------

def test_pick_event_returns_none_when_probability_fails():
    # Seed so that random.random() returns >= 0.25 (first call > threshold)
    save = _make_save()
    # Use a seed that produces a value >= 0.25 on the first call
    rng = random.Random(42)
    original_random = random.random
    # Patch random.random to always return 0.5 (above 0.25 threshold)
    random.random = lambda: 0.5
    try:
        result = pick_event(save)
    finally:
        random.random = original_random
    assert result is None


def test_pick_event_returns_none_when_candidates_empty():
    # Use a save state that meets no event conditions:
    # year=1, departments=[], buildings all 0, students=0, reputation=0
    save = _make_save(
        year=1,
        reputation={"arts": 0, "engineering": 0, "medical": 0, "humanities": 0},
        students={"enrolled": 0, "averageLevel": 1.0},
        buildings={"classroom": 0, "dormitory": 0, "laboratory": 0, "cafeteria": 0},
        departments=[],
    )

    # Force probability to pass (< 0.25) so only condition filtering is tested
    from unittest.mock import patch
    with patch("app.services.events.random") as mock_rng:
        mock_rng.random.return_value = 0.1
        result = pick_event(save)

    assert result is None


def test_pick_event_respects_conditions():
    # corp_collab needs min_departments=2; our save has 2 departments
    save = _make_save(departments=["humanities", "art"])

    original_random = random.random
    original_choices = random.choices

    # Force probability to pass and always pick corp_collab
    random.random = lambda: 0.1
    random.choices = lambda population, weights, k: [
        next(e for e in population if e.id == "corp_collab")
    ]
    try:
        result = pick_event(save)
    finally:
        random.random = original_random
        random.choices = original_choices

    assert result is not None
    assert result.id == "corp_collab"


# ---------------------------------------------------------------------------
# apply_event — budget
# ---------------------------------------------------------------------------

def test_apply_positive_event_changes_budget():
    save = _make_save(budget=200)
    event = EVENTS["corp_collab"]
    logs = apply_event(save, event)
    assert save.budget == 280
    assert any("예산" in log for log in logs)


def test_apply_negative_event_floors_at_zero():
    save = _make_save(budget=30)
    event = EVENTS["building_repair"]  # budget -60
    apply_event(save, event)
    assert save.budget == 0


# ---------------------------------------------------------------------------
# apply_event — reputation effects
# ---------------------------------------------------------------------------

def test_apply_event_reputation_leading():
    # humanities=20 is highest → paper_viral should apply to humanities
    save = _make_save(
        reputation={"arts": 5, "engineering": 5, "medical": 5, "humanities": 20}
    )
    event = EVENTS["paper_viral"]  # reputation_leading +8
    apply_event(save, event)
    assert save.reputation.humanities == 28
    # Other fields unchanged
    assert save.reputation.arts == 5
    assert save.reputation.engineering == 5
    assert save.reputation.medical == 5


def test_apply_event_reputation_each():
    save = _make_save(
        reputation={"arts": 10, "engineering": 10, "medical": 10, "humanities": 10}
    )
    event = EVENTS["edu_award"]  # reputation_each +2
    apply_event(save, event)
    assert save.reputation.arts == 12
    assert save.reputation.engineering == 12
    assert save.reputation.medical == 12
    assert save.reputation.humanities == 12


# ---------------------------------------------------------------------------
# apply_event — choice events
# ---------------------------------------------------------------------------

def test_apply_choice_event_a():
    save = _make_save(budget=100)
    event = EVENTS["big_donation"]  # choice A: budget +200
    apply_event(save, event, choice="a")
    assert save.budget == 300


def test_apply_choice_event_b():
    save = _make_save(
        reputation={"arts": 5, "engineering": 5, "medical": 5, "humanities": 5}
    )
    event = EVENTS["big_donation"]  # choice B: reputation_each +4
    apply_event(save, event, choice="b")
    assert save.reputation.arts == 9
    assert save.reputation.engineering == 9
    assert save.reputation.medical == 9
    assert save.reputation.humanities == 9


# ---------------------------------------------------------------------------
# apply_event — bonus_freshmen
# ---------------------------------------------------------------------------

def test_apply_bonus_freshmen():
    save = _make_save(
        reputation={"arts": 20, "engineering": 20, "medical": 10, "humanities": 10},
    )
    # Ensure bonus_freshmen starts at 0
    save.bonus_freshmen = 0
    event = EVENTS["applicant_surge"]  # bonus_freshmen +15
    apply_event(save, event)
    assert save.bonus_freshmen == 15
