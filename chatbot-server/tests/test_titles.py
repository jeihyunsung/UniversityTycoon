from __future__ import annotations

from app.models.schemas import (
    AdmissionCriteria, BuildingState, ReputationState, SaveState, StudentState,
)
from app.services.titles import compute_dynamic_title


def _make_save(**overrides) -> SaveState:
    defaults = dict(
        userId="test", year=1, month=1, budget=480,
        reputation=ReputationState(arts=6, engineering=6, medical=6, humanities=12),
        students=StudentState(enrolled=72, averageLevel=5.0),
        admissionPolicy="normal",
        admissionCriteria=AdmissionCriteria(math=5, science=5, english=5, korean=5),
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0),
        departments=["humanities"], logs=[],
        pendingEvent=None, bonusFreshmen=0,
        completedMilestones=["first_step"], activeQuestLines=[], completedQuests=[],
        title="신생 대학", admissionChanged=False,
    )
    defaults.update(overrides)
    return SaveState.model_validate(defaults)


def test_default_title():
    save = _make_save()
    assert compute_dynamic_title(save) == "작은 대학"


def test_growing_title():
    save = _make_save(reputation=ReputationState(arts=10, engineering=10, medical=10, humanities=12))
    assert compute_dynamic_title(save) == "성장하는 대학"


def test_research_title():
    save = _make_save(
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=3, cafeteria=0),
        departments=["humanities", "computer", "medical"],  # 3 depts * 2 = 6, + lab 3*10 = 36
    )
    assert compute_dynamic_title(save) == "연구 특화 대학"


def test_education_title():
    save = _make_save(
        buildings=BuildingState(classroom=4, dormitory=1, laboratory=0, cafeteria=1),
        departments=["humanities", "computer", "medical"],  # classroom*8=32 + cafeteria*2=2 + dept boost=15 = 49
    )
    assert compute_dynamic_title(save) == "교육 특화 대학"


def test_field_title_arts():
    save = _make_save(reputation=ReputationState(arts=35, engineering=10, medical=10, humanities=10))
    assert compute_dynamic_title(save) == "예체능 명문"


def test_field_title_engineering():
    save = _make_save(reputation=ReputationState(arts=10, engineering=35, medical=10, humanities=10))
    assert compute_dynamic_title(save) == "공학 명문"


def test_business_title():
    save = _make_save(budget=1200)
    assert compute_dynamic_title(save) == "사업형 대학"


def test_large_title():
    save = _make_save(students=StudentState(enrolled=220, averageLevel=5.0))
    assert compute_dynamic_title(save) == "대규모 대학"


def test_priority_order():
    # Meets both research (priority 1) and field (priority 3)
    save = _make_save(
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=3, cafeteria=0),
        departments=["humanities", "computer", "medical"],
        reputation=ReputationState(arts=5, engineering=35, medical=5, humanities=5),
    )
    assert compute_dynamic_title(save) == "연구 특화 대학"  # Priority 1 wins
