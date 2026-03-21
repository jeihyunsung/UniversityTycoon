"""Unit tests for the graduation event (_apply_graduation fires in February)."""
from __future__ import annotations

import pytest

from app.repositories.in_memory import InMemorySaveRepository
from app.services.game_engine import GameEngine

from tests.conftest import make_save, make_webhook


@pytest.mark.asyncio
async def test_graduation_fires_in_february(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    """Advancing from month 1 → 2 should trigger graduation and include '졸업생' in logs."""
    await repo.put(user_key, make_save(user_key, month=1, enrolled=100))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = await engine.advance_turn(webhook, repo)

    assert any("졸업생" in log for log in result.logs)


@pytest.mark.asyncio
async def test_graduation_distributes_to_leading_field(
    engine: GameEngine, repo: InMemorySaveRepository, user_key: str
) -> None:
    """Reputation increase from graduation should go to the field with the highest current rep."""
    # arts dominates — reputation gain should land on arts
    save = make_save(
        user_key,
        month=1,
        enrolled=100,
        arts=100,
        engineering=6,
        medical=6,
        humanities=6,
        departments=["art", "humanities"],
    )
    await repo.put(user_key, save)
    arts_before = save.reputation.arts
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = await engine.advance_turn(webhook, repo)

    assert result.save is not None
    assert result.save.reputation.arts > arts_before


@pytest.mark.asyncio
async def test_graduation_reduces_students(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    """Enrolled count should decrease after graduation fires in February."""
    initial_enrolled = 120
    await repo.put(user_key, make_save(user_key, month=1, enrolled=initial_enrolled))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = await engine.advance_turn(webhook, repo)

    assert result.save is not None
    # After graduation (month 2) admission hasn't run yet, so enrolled < initial
    assert result.save.students.enrolled < initial_enrolled
