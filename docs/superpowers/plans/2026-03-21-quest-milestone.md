# Quest & Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sequential milestone system (8 milestones for 1st year onboarding) and specialization quest lines (4 fields × 3 stages) with rewards, titles, and a quest status endpoint.

**Architecture:** Independent `quests.py` module with check/apply logic. Integrates into `advance_turn`, `build`, `department`, `admission` via a single `check_and_apply(save)` call. Imports shared helpers from `events.py`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-03-21-quest-milestone-design.md`

---

## Parallel Execution Map

```
Phase 1 (parallel):
  Task 1: SaveState schema changes (5 new fields + admission_changed flag)
  Task 2: quests.py core module + unit tests

Phase 2 (after Phase 1):
  Task 3: Integrate quests into game_engine.py

Phase 3 (after Task 3):
  Task 4: API endpoint (/quests) + integration tests
```

---

## File Structure

```
chatbot-server/
  app/
    models/
      schemas.py              # MODIFY: add 5 fields to SaveState
      db_models.py            # MODIFY: add 5 columns to GameSaveRow
    repositories/
      postgres.py             # MODIFY: serialize/deserialize new fields
    services/
      quests.py               # CREATE: QuestDefinition, MILESTONES, QUESTS, check_and_apply, get_quest_summary, get_quest_list
      events.py               # MODIFY: export _total_buildings, _total_reputation, _leading_field as public functions
      game_engine.py           # MODIFY: integrate check_and_apply, add quests method, update _initial_save, admission sets flag
    api/
      routes/kakao.py          # MODIFY: add quests endpoint
  tests/
    test_quests.py             # CREATE: quest logic unit tests
    test_game_engine.py        # MODIFY: quest integration tests
    test_api.py                # MODIFY: quest API test
```

---

### Task 1: SaveState Schema Changes

**Files:**
- Modify: `chatbot-server/app/models/schemas.py`
- Modify: `chatbot-server/app/models/db_models.py`
- Modify: `chatbot-server/app/repositories/postgres.py`

- [ ] **Step 1: Add 5 fields to SaveState**

In `chatbot-server/app/models/schemas.py`, add to SaveState after `bonus_freshmen`:

```python
completed_milestones: list[str] = Field(default_factory=list, alias="completedMilestones")
active_quest_lines: list[str] = Field(default_factory=list, alias="activeQuestLines")
completed_quests: list[str] = Field(default_factory=list, alias="completedQuests")
title: str = Field(default="신생 대학", alias="title")
admission_changed: bool = Field(default=False, alias="admissionChanged")
```

- [ ] **Step 2: Add columns to GameSaveRow**

In `chatbot-server/app/models/db_models.py`, add:

```python
completed_milestones: Mapped[list] = mapped_column(JSON, default=list)
active_quest_lines: Mapped[list] = mapped_column(JSON, default=list)
completed_quests: Mapped[list] = mapped_column(JSON, default=list)
title: Mapped[str] = mapped_column(String(64), default="신생 대학")
admission_changed: Mapped[bool] = mapped_column(default=False)
```

Add `Boolean` to SQLAlchemy imports if needed.

- [ ] **Step 3: Update PostgresSaveRepository**

In `put()`:
```python
row.completed_milestones = list(save.completed_milestones)
row.active_quest_lines = list(save.active_quest_lines)
row.completed_quests = list(save.completed_quests)
row.title = save.title
row.admission_changed = save.admission_changed
```

In `_row_to_save()` / `_row_to_state()`:
```python
completedMilestones=row.completed_milestones or [],
activeQuestLines=row.active_quest_lines or [],
completedQuests=row.completed_quests or [],
title=row.title or "신생 대학",
admissionChanged=row.admission_changed or False,
```

- [ ] **Step 4: Run existing tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/ -v`
Expected: All 35 tests PASS

- [ ] **Step 5: Commit**

```bash
git add chatbot-server/app/models/ chatbot-server/app/repositories/postgres.py
git commit -m "feat: add quest/milestone fields to SaveState"
```

---

### Task 2: quests.py Core Module

**Files:**
- Modify: `chatbot-server/app/services/events.py` (export helpers)
- Create: `chatbot-server/app/services/quests.py`
- Create: `chatbot-server/tests/test_quests.py`

- [ ] **Step 1: Export helper functions from events.py**

In `chatbot-server/app/services/events.py`, rename private helpers to public:
- `_total_buildings` → `total_buildings`
- `_total_reputation` → `total_reputation`
- `_leading_field` → `leading_field`

Update all internal references in events.py. These are already called from `_check_conditions` and `apply_event`.

- [ ] **Step 2: Create quests.py**

```python
# chatbot-server/app/services/quests.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models.schemas import SaveState
from app.services.events import total_buildings, total_reputation, leading_field, compute_education_power


@dataclass(frozen=True)
class QuestDefinition:
    id: str
    name: str
    description: str
    quest_type: Literal["milestone", "specialization"]
    field: str | None
    conditions: dict[str, int | bool]
    rewards: dict[str, int | str]
    prerequisite: str | None


MILESTONES: list[QuestDefinition] = [
    QuestDefinition(
        id="first_step", name="첫 걸음", description="대학 운영을 시작했습니다.",
        quest_type="milestone", field=None,
        conditions={}, rewards={"title": "신생 대학"},
        prerequisite=None,
    ),
    QuestDefinition(
        id="campus_expand", name="캠퍼스 확장", description="건물을 3개 이상 보유하세요.",
        quest_type="milestone", field=None,
        conditions={"min_buildings": 3}, rewards={"budget": 50},
        prerequisite="first_step",
    ),
    QuestDefinition(
        id="study_begins", name="학문의 시작", description="학과를 2개 이상 개설하세요.",
        quest_type="milestone", field=None,
        conditions={"min_departments": 2}, rewards={"budget": 30, "reputation_leading": 3},
        prerequisite="campus_expand",
    ),
    QuestDefinition(
        id="admission_strategist", name="입학 전략가", description="입학 정책을 변경해 보세요.",
        quest_type="milestone", field=None,
        conditions={"admission_changed": True}, rewards={"budget": 30},
        prerequisite="study_begins",
    ),
    QuestDefinition(
        id="first_graduation", name="첫 졸업식", description="첫 졸업 시즌을 경험하세요.",
        quest_type="milestone", field=None,
        conditions={"min_year": 2}, rewards={"budget": 80, "title": "교육자"},
        prerequisite="admission_strategist",
    ),
    QuestDefinition(
        id="growing_campus", name="성장하는 캠퍼스", description="건물을 5개 이상 보유하세요.",
        quest_type="milestone", field=None,
        conditions={"min_buildings": 5}, rewards={"budget": 60},
        prerequisite="first_graduation",
    ),
    QuestDefinition(
        id="dept_diversity", name="학과 다양화", description="학과를 3개 이상 개설하세요.",
        quest_type="milestone", field=None,
        conditions={"min_departments": 3}, rewards={"budget": 100, "title": "종합 대학"},
        prerequisite="growing_campus",
    ),
    QuestDefinition(
        id="first_anniversary", name="1주년", description="모든 기초 마일스톤을 완료하세요.",
        quest_type="milestone", field=None,
        conditions={"min_year": 2}, rewards={"title": "1주년 대학"},
        prerequisite="dept_diversity",
    ),
]

_SPEC_QUESTS: list[QuestDefinition] = [
    # --- arts ---
    QuestDefinition(id="arts_1", name="예술의 꽃", description="예체능 명성 20 이상",
                    quest_type="specialization", field="arts",
                    conditions={"min_reputation_arts": 20}, rewards={"budget": 60, "title": "예술 대학"},
                    prerequisite=None),
    QuestDefinition(id="arts_2", name="축제의 대학", description="식당 2개 + 예체능 명성 35 이상",
                    quest_type="specialization", field="arts",
                    conditions={"min_cafeteria": 2, "min_reputation_arts": 35}, rewards={"budget": 120, "reputation_arts": 5},
                    prerequisite="arts_1"),
    QuestDefinition(id="arts_3", name="예술 명문", description="예체능 명성 60 이상",
                    quest_type="specialization", field="arts",
                    conditions={"min_reputation_arts": 60}, rewards={"budget": 200, "title": "예술 명문대"},
                    prerequisite="arts_2"),
    # --- engineering ---
    QuestDefinition(id="eng_1", name="기술의 요람", description="공학 명성 20 이상",
                    quest_type="specialization", field="engineering",
                    conditions={"min_reputation_engineering": 20}, rewards={"budget": 60, "title": "공학 대학"},
                    prerequisite=None),
    QuestDefinition(id="eng_2", name="산학협력 선도", description="연구소 2개 + 공학 명성 35 이상",
                    quest_type="specialization", field="engineering",
                    conditions={"min_labs": 2, "min_reputation_engineering": 35}, rewards={"budget": 120, "reputation_engineering": 5},
                    prerequisite="eng_1"),
    QuestDefinition(id="eng_3", name="공학 명문", description="공학 명성 60 이상",
                    quest_type="specialization", field="engineering",
                    conditions={"min_reputation_engineering": 60}, rewards={"budget": 200, "title": "공학 명문대"},
                    prerequisite="eng_2"),
    # --- medical ---
    QuestDefinition(id="med_1", name="생명의 학교", description="의학 명성 20 이상",
                    quest_type="specialization", field="medical",
                    conditions={"min_reputation_medical": 20}, rewards={"budget": 60, "title": "의학 대학"},
                    prerequisite=None),
    QuestDefinition(id="med_2", name="연구 중심 병원", description="연구소 2개 + 의학 명성 35 이상",
                    quest_type="specialization", field="medical",
                    conditions={"min_labs": 2, "min_reputation_medical": 35}, rewards={"budget": 120, "reputation_medical": 5},
                    prerequisite="med_1"),
    QuestDefinition(id="med_3", name="의학 명문", description="의학 명성 60 이상",
                    quest_type="specialization", field="medical",
                    conditions={"min_reputation_medical": 60}, rewards={"budget": 200, "title": "의학 명문대"},
                    prerequisite="med_2"),
    # --- humanities ---
    QuestDefinition(id="hum_1", name="지성의 전당", description="기초학문 명성 20 이상",
                    quest_type="specialization", field="humanities",
                    conditions={"min_reputation_humanities": 20}, rewards={"budget": 60, "title": "인문학 대학"},
                    prerequisite=None),
    QuestDefinition(id="hum_2", name="학술 도시", description="강의실 3개 + 기초학문 명성 35 이상",
                    quest_type="specialization", field="humanities",
                    conditions={"min_classrooms": 3, "min_reputation_humanities": 35}, rewards={"budget": 120, "reputation_humanities": 5},
                    prerequisite="hum_1"),
    QuestDefinition(id="hum_3", name="인문 명문", description="기초학문 명성 60 이상",
                    quest_type="specialization", field="humanities",
                    conditions={"min_reputation_humanities": 60}, rewards={"budget": 200, "title": "인문 명문대"},
                    prerequisite="hum_2"),
]

QUESTS: dict[str, QuestDefinition] = {q.id: q for q in MILESTONES + _SPEC_QUESTS}


def _check_condition(quest: QuestDefinition, save: SaveState) -> bool:
    cond = quest.conditions
    if "min_buildings" in cond and total_buildings(save) < cond["min_buildings"]:
        return False
    if "min_departments" in cond and len(save.departments) < cond["min_departments"]:
        return False
    if "min_year" in cond and save.year < cond["min_year"]:
        return False
    if "admission_changed" in cond and not save.admission_changed:
        return False
    if "min_labs" in cond and save.buildings.laboratory < cond["min_labs"]:
        return False
    if "min_cafeteria" in cond and save.buildings.cafeteria < cond["min_cafeteria"]:
        return False
    if "min_classrooms" in cond and save.buildings.classroom < cond["min_classrooms"]:
        return False
    if "min_reputation_arts" in cond and save.reputation.arts < cond["min_reputation_arts"]:
        return False
    if "min_reputation_engineering" in cond and save.reputation.engineering < cond["min_reputation_engineering"]:
        return False
    if "min_reputation_medical" in cond and save.reputation.medical < cond["min_reputation_medical"]:
        return False
    if "min_reputation_humanities" in cond and save.reputation.humanities < cond["min_reputation_humanities"]:
        return False
    return True


def _apply_reward(save: SaveState, rewards: dict[str, int | str]) -> list[str]:
    logs: list[str] = []
    for key, value in rewards.items():
        if key == "budget" and isinstance(value, int):
            save.budget += value
            logs.append(f"예산 +{value}G")
        elif key == "title" and isinstance(value, str):
            save.title = value
            logs.append(f"칭호 획득: {value}")
        elif key == "reputation_leading" and isinstance(value, int):
            field = leading_field(save)
            current = getattr(save.reputation, field)
            setattr(save.reputation, field, current + value)
            label = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}[field]
            logs.append(f"{label} 명성 +{value}")
        elif key.startswith("reputation_") and isinstance(value, int):
            field = key.replace("reputation_", "")
            if hasattr(save.reputation, field):
                current = getattr(save.reputation, field)
                setattr(save.reputation, field, current + value)
                label = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}.get(field, field)
                logs.append(f"{label} 명성 +{value}")
    return logs


def _activate_quest_lines(save: SaveState) -> None:
    if save.active_quest_lines:
        return
    fields = sorted(
        [("arts", save.reputation.arts), ("engineering", save.reputation.engineering),
         ("medical", save.reputation.medical), ("humanities", save.reputation.humanities)],
        key=lambda x: x[1], reverse=True,
    )
    save.active_quest_lines = [f[0] for f in fields[:2]]


def check_and_apply(save: SaveState) -> list[str]:
    all_completed = save.completed_milestones + save.completed_quests
    logs: list[str] = []

    # Check milestones sequentially
    for ms in MILESTONES:
        if ms.id in all_completed:
            continue
        if ms.prerequisite and ms.prerequisite not in all_completed:
            break  # Sequential — stop at first unmet prerequisite
        if not _check_condition(ms, save):
            break  # Sequential — stop at first unmet condition
        save.completed_milestones.append(ms.id)
        all_completed.append(ms.id)
        reward_logs = _apply_reward(save, ms.rewards)
        logs.append(f"🏆 마일스톤 달성: {ms.name}")
        logs.extend(reward_logs)
        # Activate quest lines on milestone 8
        if ms.id == "first_anniversary":
            _activate_quest_lines(save)
            field_labels = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}
            line_names = [field_labels[f] for f in save.active_quest_lines]
            logs.append(f"🎯 특화 퀘스트 해금: {', '.join(line_names)}")

    # Check specialization quests
    for quest in _SPEC_QUESTS:
        if quest.field not in save.active_quest_lines:
            continue
        if quest.id in all_completed:
            continue
        if quest.prerequisite and quest.prerequisite not in all_completed:
            continue
        if not _check_condition(quest, save):
            continue
        save.completed_quests.append(quest.id)
        all_completed.append(quest.id)
        reward_logs = _apply_reward(save, quest.rewards)
        logs.append(f"⭐ 퀘스트 달성: {quest.name}")
        logs.extend(reward_logs)

    return logs


def get_quest_summary(save: SaveState) -> str:
    all_completed = set(save.completed_milestones + save.completed_quests)

    # Check next milestone
    for ms in MILESTONES:
        if ms.id not in all_completed:
            progress = _get_progress_text(ms, save)
            return f"📋 다음 목표: {ms.name} {progress}"

    # Check next specialization quest
    for quest in _SPEC_QUESTS:
        if quest.field not in save.active_quest_lines:
            continue
        if quest.id in all_completed:
            continue
        if quest.prerequisite and quest.prerequisite not in all_completed:
            continue
        progress = _get_progress_text(quest, save)
        return f"📋 다음 목표: {quest.name} {progress}"

    return "🎓 모든 퀘스트 완료!"


def _get_progress_text(quest: QuestDefinition, save: SaveState) -> str:
    parts = []
    cond = quest.conditions
    if "min_buildings" in cond:
        parts.append(f"건물 {total_buildings(save)}/{cond['min_buildings']}")
    if "min_departments" in cond:
        parts.append(f"학과 {len(save.departments)}/{cond['min_departments']}")
    if "min_year" in cond:
        parts.append(f"{save.year}/{cond['min_year']}년차")
    if "admission_changed" in cond:
        parts.append("정책 변경 " + ("완료" if save.admission_changed else "미완료"))
    for key in ("min_reputation_arts", "min_reputation_engineering", "min_reputation_medical", "min_reputation_humanities"):
        if key in cond:
            field = key.replace("min_reputation_", "")
            label = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}[field]
            current = getattr(save.reputation, field)
            parts.append(f"{label} {current}/{cond[key]}")
    if "min_labs" in cond:
        parts.append(f"연구소 {save.buildings.laboratory}/{cond['min_labs']}")
    if "min_cafeteria" in cond:
        parts.append(f"식당 {save.buildings.cafeteria}/{cond['min_cafeteria']}")
    if "min_classrooms" in cond:
        parts.append(f"강의실 {save.buildings.classroom}/{cond['min_classrooms']}")
    return f"({', '.join(parts)})" if parts else ""


def get_quest_list(save: SaveState) -> list[dict]:
    all_completed = set(save.completed_milestones + save.completed_quests)
    result = []

    result.append({"section": "마일스톤"})
    for ms in MILESTONES:
        if ms.id in all_completed:
            status = "✅"
        elif ms.prerequisite and ms.prerequisite not in all_completed:
            status = "🔒"
        elif _check_condition(ms, save):
            status = "⭐ 달성 가능"
        else:
            status = _get_progress_text(ms, save)
        result.append({"name": ms.name, "status": status})

    if save.active_quest_lines:
        field_labels = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}
        for line in save.active_quest_lines:
            result.append({"section": f"특화: {field_labels[line]}"})
            for quest in _SPEC_QUESTS:
                if quest.field != line:
                    continue
                if quest.id in all_completed:
                    status = "✅"
                elif quest.prerequisite and quest.prerequisite not in all_completed:
                    status = "🔒"
                elif _check_condition(quest, save):
                    status = "⭐ 달성 가능"
                else:
                    status = _get_progress_text(quest, save)
                result.append({"name": quest.name, "status": status})

    return result
```

- [ ] **Step 3: Create test_quests.py**

```python
# chatbot-server/tests/test_quests.py
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
```

- [ ] **Step 4: Run tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/test_quests.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add chatbot-server/app/services/events.py chatbot-server/app/services/quests.py chatbot-server/tests/test_quests.py
git commit -m "feat: add quests module with milestones and specialization quest lines"
```

---

### Task 3: Integrate Quests into GameEngine

**Files:**
- Modify: `chatbot-server/app/services/game_engine.py`
- Modify: `chatbot-server/tests/test_game_engine.py`
- Modify: `chatbot-server/tests/conftest.py`

- [ ] **Step 1: Update _initial_save**

Pre-populate first milestone and title:
```python
completedMilestones=["first_step"],
activeQuestLines=[],
completedQuests=[],
title="신생 대학",
admissionChanged=False,
```

- [ ] **Step 2: Import and integrate check_and_apply**

Add import at top of game_engine.py:
```python
from app.services.quests import check_and_apply as check_quests, get_quest_summary
```

In `advance_turn`, after event judgment and before `save.logs = [...]`:
```python
quest_logs = check_quests(save)
if quest_logs:
    logs.extend(quest_logs)
```

In `build`, `department` methods, after the action is applied and before `await repo.put(...)`:
```python
quest_logs = check_quests(save)
if quest_logs:
    save.logs = [*quest_logs, *save.logs][:5]
```

In `admission` method, set the flag before saving:
```python
save.admission_changed = True
```
And add quest check:
```python
quest_logs = check_quests(save)
if quest_logs:
    save.logs = [*quest_logs, *save.logs][:5]
```

- [ ] **Step 3: Update load_status with quest summary**

In `load_status`, add quest summary to message:
```python
quest_summary = get_quest_summary(save)
```
Include in message string:
```python
message=(
    f"{save.year}년 {MONTH_LABELS[save.month]}입니다. "
    f"예산 {save.budget}G / 총 명성 {total_reputation} / 재학생 {save.students.enrolled}명\n"
    f"{quest_summary}"
),
```

Add "퀘스트" to quickReplies:
```python
quickReplies=["다음 달 진행", "건물 건설", "학과 개설", "입학 정책", "퀘스트", "지난 결과 보기"],
```

- [ ] **Step 4: Add quests method to GameEngine**

```python
async def quests(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
    save = await self._get_or_create(request.user.id, repo)
    from app.services.quests import get_quest_list
    quest_list = get_quest_list(save)

    lines = []
    for item in quest_list:
        if "section" in item:
            lines.append(f"\n【{item['section']}】")
        else:
            lines.append(f"  {item['status']} {item['name']}")

    return GameResult(
        message=f"🎓 {save.title}\n" + "\n".join(lines),
        quickReplies=["내 대학 현황", "다음 달 진행", "메인 메뉴"],
        save=save,
    )
```

- [ ] **Step 5: Update conftest.py make_save**

Add keyword args:
```python
completed_milestones: list[str] | None = None,
active_quest_lines: list[str] | None = None,
completed_quests: list[str] | None = None,
title: str = "신생 대학",
admission_changed: bool = False,
```

And in dict:
```python
"completedMilestones": completed_milestones if completed_milestones is not None else ["first_step"],
"activeQuestLines": active_quest_lines if active_quest_lines is not None else [],
"completedQuests": completed_quests if completed_quests is not None else [],
"title": title,
"admissionChanged": admission_changed,
```

- [ ] **Step 6: Add game_engine quest tests**

```python
async def test_build_triggers_milestone(engine, repo, user_key):
    save = make_save(user_key, buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0))
    await repo.put(user_key, save)
    # Build a lab → total 3 buildings → campus_expand milestone
    result = await engine.build(
        make_webhook(user_key, action_name="ACTION_BUILD_LAB"), repo
    )
    assert "campus_expand" in result.save.completed_milestones


async def test_admission_sets_changed_flag(engine, repo, user_key):
    save = make_save(user_key)
    await repo.put(user_key, save)
    result = await engine.admission(
        make_webhook(user_key, action_name="ACTION_ADMISSION_HARD"), repo
    )
    assert result.save.admission_changed is True


async def test_load_status_includes_quest_summary(engine, repo, user_key):
    save = make_save(user_key)
    await repo.put(user_key, save)
    result = await engine.load_status(make_webhook(user_key), repo)
    assert "다음 목표" in result.message or "퀘스트" in result.message
```

- [ ] **Step 7: Run all tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add chatbot-server/app/services/game_engine.py chatbot-server/tests/test_game_engine.py chatbot-server/tests/conftest.py
git commit -m "feat: integrate quest system into game engine"
```

---

### Task 4: API Endpoint + Integration Tests

**Files:**
- Modify: `chatbot-server/app/api/routes/kakao.py`
- Modify: `chatbot-server/tests/test_api.py`

- [ ] **Step 1: Add quests route**

```python
@router.post("/quests")
async def quests(request: KakaoWebhookRequest, repo: SaveRepository = Depends(get_repository)) -> dict:
    result = await game_engine.quests(request, repo)
    return to_kakao_response(result)
```

- [ ] **Step 2: Add API test**

```python
async def test_quests_endpoint(client):
    user_key = "quest_test_user"
    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))
    resp = await client.post("/webhooks/kakao/quests", json=_payload(user_key))
    assert resp.status_code == 200
    text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
    assert "마일스톤" in text or "신생 대학" in text
```

- [ ] **Step 3: Run all tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add chatbot-server/app/api/routes/kakao.py chatbot-server/tests/test_api.py
git commit -m "feat: add quests API endpoint with integration test"
```
