"""Shared fixtures for GameEngine tests."""
from __future__ import annotations

import pytest

from app.models.schemas import (
    AdmissionCriteria,
    ActionPayload,
    BuildingState,
    KakaoUser,
    KakaoWebhookRequest,
    ReputationState,
    SaveState,
    StudentState,
    UserRequest,
)
from app.repositories.in_memory import InMemorySaveRepository
from app.services.game_engine import GameEngine


@pytest.fixture()
def repo() -> InMemorySaveRepository:
    """Return a fresh, empty in-memory save repository."""
    return InMemorySaveRepository()


@pytest.fixture()
def engine() -> GameEngine:
    """Return a GameEngine instance (repo is now passed per-call)."""
    return GameEngine()


@pytest.fixture()
def user_key() -> str:
    return "test-user-001"


def make_webhook(user_key: str, action_name: str = "ACTION_STATUS", params: dict | None = None) -> KakaoWebhookRequest:
    """Build a minimal KakaoWebhookRequest for testing."""
    return KakaoWebhookRequest(
        userRequest=UserRequest(user=KakaoUser(id=user_key)),
        action=ActionPayload(name=action_name, params=params or {}),
    )


@pytest.fixture()
def webhook(user_key: str) -> KakaoWebhookRequest:
    """Default webhook with ACTION_STATUS action."""
    return make_webhook(user_key)


def make_save(
    user_key: str,
    *,
    year: int = 1,
    month: int = 1,
    budget: int = 480,
    enrolled: int = 72,
    average_level: float = 5.0,
    arts: int = 6,
    engineering: int = 6,
    medical: int = 6,
    humanities: int = 12,
    classroom: int = 1,
    dormitory: int = 1,
    laboratory: int = 0,
    cafeteria: int = 0,
    departments: list[str] | None = None,
    logs: list[str] | None = None,
    admission_policy: str = "normal",
    admission_criteria: AdmissionCriteria | None = None,
    pending_event: str | None = None,
    bonus_freshmen: int = 0,
) -> SaveState:
    """Build a SaveState with sensible defaults — override only what each test needs."""
    return SaveState.model_validate(
        {
            "userId": user_key,
            "year": year,
            "month": month,
            "budget": budget,
            "reputation": {"arts": arts, "engineering": engineering, "medical": medical, "humanities": humanities},
            "students": {"averageLevel": average_level, "enrolled": enrolled},
            "admissionPolicy": admission_policy,
            "buildings": {
                "classroom": classroom,
                "dormitory": dormitory,
                "laboratory": laboratory,
                "cafeteria": cafeteria,
            },
            "departments": departments if departments is not None else ["humanities"],
            "logs": logs if logs is not None else [],
            "admissionCriteria": {
                "math": admission_criteria.math if admission_criteria else 5,
                "science": admission_criteria.science if admission_criteria else 5,
                "english": admission_criteria.english if admission_criteria else 5,
                "korean": admission_criteria.korean if admission_criteria else 5,
            },
            "pendingEvent": pending_event,
            "bonusFreshmen": bonus_freshmen,
        }
    )
