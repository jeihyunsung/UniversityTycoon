from __future__ import annotations

import pytest

from app.models.schemas import (
    AdmissionCriteria, BuildingState, ReputationState, SaveState, StudentState,
)
from app.services.quests import check_and_apply, get_quest_summary, get_quest_list, MILESTONES


def _make_save(**overrides) -> SaveState:
    defaults = dict(
        userId="test", year=1, month=1, budget=480,
        reputation=ReputationState(arts=6, engineering=6, medical=6, humanities=12),
        students=StudentState(enrolled=72, averageLevel=5.0),
        admissionPolicy="normal",
        admissionCriteria=AdmissionCriteria(math=5, science=5, english=5, korean=5),
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0),
        departments=["humanities"], logs=[],
        completedMilestones=["first_step"], activeQuestLines=[], completedQuests=[],
        title="신생 대학", admissionChanged=False,
        pendingEvent=None, bonusFreshmen=0,
    )
    defaults.update(overrides)
    return SaveState.model_validate(defaults)


def test_campus_expand_milestone():
    save = _make_save(buildings=BuildingState(classroom=1, dormitory=1, laboratory=1, cafeteria=0))
    logs = check_and_apply(save)
    assert "campus_expand" in save.completed_milestones
    assert save.budget == 530  # 480 + 50


def test_milestone_requires_prerequisite():
    # study_begins requires campus_expand, which is not completed
    save = _make_save(departments=["humanities", "computer"])
    logs = check_and_apply(save)
    assert "study_begins" not in save.completed_milestones


def test_cascading_milestones():
    # Meet conditions for milestones 2, 3, 4 at once
    save = _make_save(
        buildings=BuildingState(classroom=2, dormitory=1, laboratory=1, cafeteria=0),
        departments=["humanities", "computer"],
        admissionChanged=True,
    )
    logs = check_and_apply(save)
    assert "campus_expand" in save.completed_milestones
    assert "study_begins" in save.completed_milestones
    assert "admission_strategist" in save.completed_milestones


def test_first_anniversary_activates_quest_lines():
    save = _make_save(
        year=2,
        buildings=BuildingState(classroom=2, dormitory=1, laboratory=1, cafeteria=1),
        departments=["humanities", "computer", "art"],
        admissionChanged=True,
        completedMilestones=["first_step", "campus_expand", "study_begins",
                            "admission_strategist", "first_graduation", "growing_campus", "dept_diversity"],
    )
    logs = check_and_apply(save)
    assert "first_anniversary" in save.completed_milestones
    assert len(save.active_quest_lines) == 2


def test_quest_line_top_two_fields():
    save = _make_save(
        year=2,
        reputation=ReputationState(arts=50, engineering=40, medical=10, humanities=10),
        buildings=BuildingState(classroom=2, dormitory=1, laboratory=1, cafeteria=1),
        departments=["humanities", "computer", "art"],
        admissionChanged=True,
        completedMilestones=["first_step", "campus_expand", "study_begins",
                            "admission_strategist", "first_graduation", "growing_campus", "dept_diversity"],
    )
    check_and_apply(save)
    assert save.active_quest_lines == ["arts", "engineering"]


def test_specialization_quest_applies_reward():
    save = _make_save(
        reputation=ReputationState(arts=25, engineering=6, medical=6, humanities=12),
        activeQuestLines=["arts", "humanities"],
        completedMilestones=["first_step", "campus_expand", "study_begins",
                            "admission_strategist", "first_graduation", "growing_campus",
                            "dept_diversity", "first_anniversary"],
    )
    logs = check_and_apply(save)
    assert "arts_1" in save.completed_quests
    assert save.budget == 540  # 480 + 60
    assert save.title == "예술 대학"


def test_specialization_quest_sequential():
    # arts_2 requires arts_1 completed
    save = _make_save(
        reputation=ReputationState(arts=40, engineering=6, medical=6, humanities=12),
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=2),
        activeQuestLines=["arts", "humanities"],
        completedMilestones=["first_step", "campus_expand", "study_begins",
                            "admission_strategist", "first_graduation", "growing_campus",
                            "dept_diversity", "first_anniversary"],
    )
    check_and_apply(save)
    # arts_1 should complete (arts >= 20), then arts_2 should also complete (arts >= 35 + cafeteria >= 2)
    assert "arts_1" in save.completed_quests
    assert "arts_2" in save.completed_quests


def test_get_quest_summary_milestone():
    save = _make_save()
    summary = get_quest_summary(save)
    assert "캠퍼스 확장" in summary
    assert "건물" in summary


def test_get_quest_summary_specialization():
    save = _make_save(
        completedMilestones=["first_step", "campus_expand", "study_begins",
                            "admission_strategist", "first_graduation", "growing_campus",
                            "dept_diversity", "first_anniversary"],
        activeQuestLines=["arts", "humanities"],
    )
    summary = get_quest_summary(save)
    assert "예술의 꽃" in summary or "지성의 전당" in summary


def test_get_quest_list():
    save = _make_save()
    result = get_quest_list(save)
    assert any(item.get("section") == "마일스톤" for item in result)
    assert len(result) > 1
