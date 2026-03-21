"""Unit tests for the admission event (_apply_admission fires in March)."""
from __future__ import annotations

import pytest

from app.repositories.in_memory import InMemorySaveRepository
from app.services.game_engine import GameEngine

from tests.conftest import make_save, make_webhook


@pytest.mark.asyncio
async def test_admission_fires_in_march(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    """Advancing from month 2 → 3 should trigger admission and include '신입생' in logs."""
    await repo.put(user_key, make_save(user_key, month=2, enrolled=50))
    webhook = make_webhook(user_key, action_name="ACTION_NEXT_TURN")

    result = await engine.advance_turn(webhook, repo)

    assert any("신입생" in log for log in result.logs)


@pytest.mark.asyncio
async def test_policy_change(engine: GameEngine, repo: InMemorySaveRepository, user_key: str) -> None:
    """Calling admission() with ACTION_ADMISSION_HARD should update the policy to 'hard'."""
    await repo.put(user_key, make_save(user_key, admission_policy="normal"))
    webhook = make_webhook(user_key, action_name="ACTION_ADMISSION_HARD")

    result = await engine.admission(webhook, repo)

    assert result.ok is True
    assert result.save is not None
    assert result.save.admission_policy == "hard"
    # Criteria should also be updated to hard preset values
    assert result.save.admission_criteria.math == 7
    assert result.save.admission_criteria.science == 7
