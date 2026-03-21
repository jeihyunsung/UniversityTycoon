"""Unit tests for the core GameEngine loop."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.models.schemas import BuildingState
from app.repositories.in_memory import InMemorySaveRepository
from app.services.events import EVENTS
from app.services.game_engine import GameEngine

from tests.conftest import make_save, make_webhook


# ---------------------------------------------------------------------------
# start_game
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_game_creates_save(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    webhook = make_webhook(user_key)
    result = await engine.start_game(webhook, repo)

    assert result.ok is True
    save = await repo.get(user_key)
    assert save is not None
    assert save.budget == 480
    assert save.year == 1


# ---------------------------------------------------------------------------
# load_status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_load_status_returns_state(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    await repo.put(user_key, make_save(user_key, budget=480))
    webhook = make_webhook(user_key)

    result = await engine.load_status(webhook, repo)

    assert "예산 480G" in result.message


# ---------------------------------------------------------------------------
# advance_turn — month increment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_advance_turn_increments_month(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    await repo.put(user_key, make_save(user_key, year=1, month=1))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = await engine.advance_turn(webhook, repo)

    assert result.save is not None
    assert result.save.month == 2


@pytest.mark.asyncio
async def test_advance_turn_wraps_year(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    await repo.put(user_key, make_save(user_key, year=1, month=12))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = await engine.advance_turn(webhook, repo)

    assert result.save is not None
    assert result.save.month == 1
    assert result.save.year == 2


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_build_classroom_deducts_budget(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    initial_budget = 480
    # Mark campus_expand completed so quest reward doesn't affect budget assertion
    await repo.put(user_key, make_save(
        user_key, budget=initial_budget, classroom=1,
        completed_milestones=["first_step", "campus_expand"],
    ))
    webhook = make_webhook(user_key, action_name="ACTION_BUILD_CLASSROOM")

    result = await engine.build(webhook, repo)

    assert result.ok is True
    assert result.save is not None
    assert result.save.budget == initial_budget - 120
    assert result.save.buildings.classroom == 2


@pytest.mark.asyncio
async def test_build_insufficient_budget(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    await repo.put(user_key, make_save(user_key, budget=50))
    webhook = make_webhook(user_key, action_name="ACTION_BUILD_CLASSROOM")

    result = await engine.build(webhook, repo)

    assert result.ok is False
    assert result.error_code == "NOT_ENOUGH_BUDGET"


# ---------------------------------------------------------------------------
# department
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_department_open(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    # Start without computer science so we can open it
    await repo.put(user_key, make_save(user_key, budget=480, departments=["humanities"]))
    webhook = make_webhook(user_key, action_name="ACTION_DEPT_COMPUTER")

    result = await engine.department(webhook, repo)

    assert result.ok is True
    assert result.save is not None
    assert "computer" in result.save.departments


@pytest.mark.asyncio
async def test_department_duplicate(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    await repo.put(user_key, make_save(user_key, budget=480, departments=["computer"]))
    webhook = make_webhook(user_key, action_name="ACTION_DEPT_COMPUTER")

    result = await engine.department(webhook, repo)

    assert result.ok is False
    assert result.error_code == "ALREADY_OPENED"


# ---------------------------------------------------------------------------
# Random events integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_advance_turn_can_trigger_event(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key, year=3, departments=["humanities", "computer"], budget=500,
                     laboratory=1, cafeteria=1)
    await repo.put(user_key, save)

    with patch("app.services.events.random.random", return_value=0.1), \
         patch("app.services.events.random.choices", return_value=[EVENTS["corp_collab"]]):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert any("산학협력" in log for log in result.logs)


@pytest.mark.asyncio
async def test_choice_event_sets_pending(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key, year=3, departments=["humanities", "computer"],
                     budget=500, laboratory=1)
    await repo.put(user_key, save)

    with patch("app.services.events.random.random", return_value=0.1), \
         patch("app.services.events.random.choices", return_value=[EVENTS["big_donation"]]):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert result.save.pending_event == "big_donation"
    assert "선택 A" in result.quick_replies


@pytest.mark.asyncio
async def test_pending_event_expires_on_next_turn(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key, year=3, pending_event="big_donation")
    await repo.put(user_key, save)

    # Patch pick_event where game_engine looks it up (imported name)
    with patch("app.services.game_engine.pick_event", return_value=None):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert result.save.pending_event is None
    assert any("기회가 사라졌습니다" in log for log in result.save.logs)


@pytest.mark.asyncio
async def test_event_choice_clears_pending(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key, budget=100, pending_event="big_donation")
    await repo.put(user_key, save)

    webhook = make_webhook(user_key, action_name="EVENT_CHOICE", params={"choice": "a"})
    result = await engine.event_choice(webhook, repo)
    assert result.ok is True
    assert result.save.pending_event is None
    assert result.save.budget == 300  # +200G


@pytest.mark.asyncio
async def test_bonus_freshmen_applied_in_march(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key, month=2, bonus_freshmen=15)
    await repo.put(user_key, save)

    with patch("app.services.events.pick_event", return_value=None):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert result.save.month == 3
    assert result.save.bonus_freshmen == 0


# ---------------------------------------------------------------------------
# Quest integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_build_triggers_milestone(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key, buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0))
    await repo.put(user_key, save)
    result = await engine.build(
        make_webhook(user_key, action_name="ACTION_BUILD_LAB"), repo
    )
    assert "campus_expand" in result.save.completed_milestones


@pytest.mark.asyncio
async def test_admission_sets_changed_flag(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key)
    await repo.put(user_key, save)
    result = await engine.admission(
        make_webhook(user_key, action_name="ACTION_ADMISSION_HARD"), repo
    )
    assert result.save.admission_changed is True


@pytest.mark.asyncio
async def test_load_status_includes_quest_summary(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    save = make_save(user_key)
    await repo.put(user_key, save)
    result = await engine.load_status(make_webhook(user_key), repo)
    assert "다음 목표" in result.message or "퀘스트" in result.message
