"""Unit tests for the core GameEngine loop."""
from __future__ import annotations

import pytest

from app.repositories.in_memory import InMemorySaveRepository
from app.services.game_engine import GameEngine

from tests.conftest import make_save, make_webhook


# ---------------------------------------------------------------------------
# start_game
# ---------------------------------------------------------------------------

def test_start_game_creates_save(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    webhook = make_webhook(user_key)
    result = engine.start_game(webhook)

    assert result.ok is True
    save = repo.get(user_key)
    assert save is not None
    assert save.budget == 480
    assert save.year == 1


# ---------------------------------------------------------------------------
# load_status
# ---------------------------------------------------------------------------

def test_load_status_returns_state(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    repo.put(user_key, make_save(user_key, budget=480))
    webhook = make_webhook(user_key)

    result = engine.load_status(webhook)

    assert "예산 480G" in result.message


# ---------------------------------------------------------------------------
# advance_turn — month increment
# ---------------------------------------------------------------------------

def test_advance_turn_increments_month(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    repo.put(user_key, make_save(user_key, year=1, month=1))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = engine.advance_turn(webhook)

    assert result.save is not None
    assert result.save.month == 2


def test_advance_turn_wraps_year(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    repo.put(user_key, make_save(user_key, year=1, month=12))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = engine.advance_turn(webhook)

    assert result.save is not None
    assert result.save.month == 1
    assert result.save.year == 2


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def test_build_classroom_deducts_budget(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    initial_budget = 480
    repo.put(user_key, make_save(user_key, budget=initial_budget, classroom=1))
    webhook = make_webhook(user_key, action_name="ACTION_BUILD_CLASSROOM")

    result = engine.build(webhook)

    assert result.ok is True
    assert result.save is not None
    assert result.save.budget == initial_budget - 120
    assert result.save.buildings.classroom == 2


def test_build_insufficient_budget(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    repo.put(user_key, make_save(user_key, budget=50))
    webhook = make_webhook(user_key, action_name="ACTION_BUILD_CLASSROOM")

    result = engine.build(webhook)

    assert result.ok is False
    assert result.error_code == "NOT_ENOUGH_BUDGET"


# ---------------------------------------------------------------------------
# department
# ---------------------------------------------------------------------------

def test_department_open(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    # Start without computer science so we can open it
    repo.put(user_key, make_save(user_key, budget=480, departments=["humanities"]))
    webhook = make_webhook(user_key, action_name="ACTION_DEPT_COMPUTER")

    result = engine.department(webhook)

    assert result.ok is True
    assert result.save is not None
    assert "computer" in result.save.departments


def test_department_duplicate(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    repo.put(user_key, make_save(user_key, budget=480, departments=["computer"]))
    webhook = make_webhook(user_key, action_name="ACTION_DEPT_COMPUTER")

    result = engine.department(webhook)

    assert result.ok is False
    assert result.error_code == "ALREADY_OPENED"
