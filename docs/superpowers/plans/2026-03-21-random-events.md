# Random Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a random event system that fires during turn advancement, with positive/negative/choice event types, condition-based filtering, and weighted random selection.

**Architecture:** Independent `events.py` module handles event definitions, condition filtering, random selection, and effect application. `game_engine.py` calls into it from `advance_turn`. Choice events use `pending_event` on SaveState and a new `/event-choice` endpoint.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-03-21-random-events-design.md`

---

## Parallel Execution Map

```
Phase 1 (parallel):
  Task 1: SaveState schema changes (pending_event, bonus_freshmen)
  Task 2: events.py core module (EventDefinition, EVENTS, pick_event, apply_event)

Phase 2 (sequential, after Phase 1):
  Task 3: Integrate events into game_engine.py (advance_turn + event_choice + bonus_freshmen)

Phase 3 (after Task 3):
  Task 4: API endpoint + integration tests
```

---

## File Structure

```
chatbot-server/
  app/
    models/
      schemas.py              # MODIFY: add pending_event, bonus_freshmen to SaveState
      db_models.py            # MODIFY: add pending_event, bonus_freshmen columns
    repositories/
      postgres.py             # MODIFY: serialize/deserialize new fields
    services/
      events.py               # CREATE: EventDefinition, EVENTS, compute_education_power, pick_event, apply_event
      game_engine.py           # MODIFY: advance_turn integration, event_choice method, _apply_admission bonus
    api/
      routes/kakao.py          # MODIFY: add event-choice endpoint
  tests/
    test_events.py             # CREATE: unit tests for events module
    test_game_engine.py        # MODIFY: add event integration tests
    test_api.py                # MODIFY: add event-choice API test
```

---

### Task 1: SaveState Schema Changes

**Files:**
- Modify: `chatbot-server/app/models/schemas.py`
- Modify: `chatbot-server/app/models/db_models.py`
- Modify: `chatbot-server/app/repositories/postgres.py`

- [ ] **Step 1: Add pending_event and bonus_freshmen to SaveState**

In `chatbot-server/app/models/schemas.py`, add two fields to `SaveState` after `admission_criteria`:

```python
pending_event: str | None = Field(default=None, alias="pendingEvent")
bonus_freshmen: int = Field(default=0, alias="bonusFreshmen")
```

- [ ] **Step 2: Add columns to GameSaveRow**

In `chatbot-server/app/models/db_models.py`, add to `GameSaveRow`:

```python
pending_event: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
bonus_freshmen: Mapped[int] = mapped_column(Integer, default=0)
```

- [ ] **Step 3: Update PostgresSaveRepository**

In `chatbot-server/app/repositories/postgres.py`:

In `put()`, add after `row.logs = ...`:
```python
row.pending_event = save.pending_event
row.bonus_freshmen = save.bonus_freshmen
```

In `_row_to_save()`, add to the SaveState constructor after `logs=`:
```python
pendingEvent=row.pending_event,
bonusFreshmen=row.bonus_freshmen,
```

- [ ] **Step 4: Run existing tests to verify no breakage**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/ -v`
Expected: All 17 tests PASS (new fields have defaults so existing tests unaffected)

- [ ] **Step 5: Commit**

```bash
git add chatbot-server/app/models/schemas.py chatbot-server/app/models/db_models.py chatbot-server/app/repositories/postgres.py
git commit -m "feat: add pending_event and bonus_freshmen fields to SaveState"
```

---

### Task 2: Events Core Module

**Files:**
- Create: `chatbot-server/app/services/events.py`
- Create: `chatbot-server/tests/test_events.py`

- [ ] **Step 1: Create events.py with EventDefinition and EVENTS**

```python
# chatbot-server/app/services/events.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from app.models.schemas import SaveState


@dataclass(frozen=True)
class EventDefinition:
    id: str
    name: str
    description: str
    event_type: Literal["positive", "negative", "choice"]
    effects: dict[str, int]
    conditions: dict[str, int]
    weight: int
    choice_b_effects: dict[str, int] | None = None
    choice_a_label: str | None = None
    choice_b_label: str | None = None


_EVENT_LIST: list[EventDefinition] = [
    # --- Positive ---
    EventDefinition(
        id="corp_collab", name="기업 산학협력 체결",
        description="대기업과 산학협력 협약을 맺었습니다!",
        event_type="positive", effects={"budget": 80},
        conditions={"min_departments": 2}, weight=10,
    ),
    EventDefinition(
        id="alumni_donation", name="졸업생 CEO 기부",
        description="졸업생이 대표이사가 되어 모교에 기부했습니다!",
        event_type="positive", effects={"budget": 150},
        conditions={"min_year": 2}, weight=8,
    ),
    EventDefinition(
        id="paper_viral", name="교수 논문 화제",
        description="우리 대학 교수의 논문이 화제가 되고 있습니다!",
        event_type="positive", effects={"reputation_leading": 8},
        conditions={"min_labs": 1}, weight=10,
    ),
    EventDefinition(
        id="local_festival", name="지역 축제 개최",
        description="대학 주변에서 축제가 열려 인지도가 올랐습니다!",
        event_type="positive", effects={"reputation_arts": 5},
        conditions={"min_cafeteria": 1}, weight=8,
    ),
    EventDefinition(
        id="edu_award", name="교육부 우수 평가",
        description="교육부로부터 우수 교육기관 평가를 받았습니다!",
        event_type="positive", effects={"reputation_each": 2},
        conditions={"min_education_power": 30, "min_year": 2}, weight=7,
    ),
    EventDefinition(
        id="applicant_surge", name="신입생 지원 폭증",
        description="우리 대학의 명성이 높아져 지원자가 폭증합니다!",
        event_type="positive", effects={"bonus_freshmen": 15},
        conditions={"min_reputation": 50}, weight=7,
    ),
    # --- Negative ---
    EventDefinition(
        id="building_repair", name="건물 보수 필요",
        description="노후 건물의 긴급 보수가 필요합니다.",
        event_type="negative", effects={"budget": -60},
        conditions={"min_buildings": 4}, weight=6,
    ),
    EventDefinition(
        id="prof_departure", name="교수 이직",
        description="핵심 교수가 다른 대학으로 이직했습니다.",
        event_type="negative", effects={"reputation_leading": -5},
        conditions={"min_departments": 2}, weight=5,
    ),
    EventDefinition(
        id="tuition_protest", name="등록금 동결 시위",
        description="학생들이 등록금 동결을 요구하며 시위합니다.",
        event_type="negative", effects={"budget": -80},
        conditions={"min_students": 100}, weight=4,
    ),
    EventDefinition(
        id="equipment_failure", name="연구 장비 고장",
        description="연구소 장비가 고장나 수리비가 필요합니다.",
        event_type="negative", effects={"budget": -40},
        conditions={"min_labs": 1}, weight=5,
    ),
    # --- Choice ---
    EventDefinition(
        id="big_donation", name="대기업 기부 제안",
        description="대기업에서 거액의 기부를 제안했습니다. 수락하면 자금을, 거절하면 독립 명성을 얻습니다.",
        event_type="choice",
        effects={"budget": 200},
        choice_b_effects={"reputation_each": 4},
        choice_a_label="수락", choice_b_label="거절",
        conditions={"min_year": 3}, weight=3,
    ),
    EventDefinition(
        id="star_prof", name="유명 교수 스카우트",
        description="세계적 석학을 스카우트할 기회입니다. 채용하면 비용이 들지만 명성이 오릅니다.",
        event_type="choice",
        effects={"budget": -100, "reputation_leading": 10},
        choice_b_effects={},
        choice_a_label="채용", choice_b_label="패스",
        conditions={"min_labs": 1}, weight=3,
    ),
    EventDefinition(
        id="club_support", name="학생 동아리 지원 요청",
        description="학생 동아리가 지원금을 요청합니다. 지원하면 예체능 명성이 오릅니다.",
        event_type="choice",
        effects={"budget": -50, "reputation_arts": 8},
        choice_b_effects={},
        choice_a_label="지원", choice_b_label="거절",
        conditions={"min_students": 80}, weight=3,
    ),
]

EVENTS: dict[str, EventDefinition] = {e.id: e for e in _EVENT_LIST}


def compute_education_power(save: SaveState) -> int:
    from app.services.game_engine import DEPARTMENTS
    dept_boost = sum(DEPARTMENTS[d].education_boost for d in save.departments)
    return save.buildings.classroom * 8 + save.buildings.cafeteria * 2 + dept_boost


def _total_buildings(save: SaveState) -> int:
    return (
        save.buildings.classroom + save.buildings.dormitory
        + save.buildings.laboratory + save.buildings.cafeteria
    )


def _total_reputation(save: SaveState) -> int:
    return (
        save.reputation.arts + save.reputation.engineering
        + save.reputation.medical + save.reputation.humanities
    )


def _check_conditions(event: EventDefinition, save: SaveState) -> bool:
    cond = event.conditions
    if "min_departments" in cond and len(save.departments) < cond["min_departments"]:
        return False
    if "min_year" in cond and save.year < cond["min_year"]:
        return False
    if "min_buildings" in cond and _total_buildings(save) < cond["min_buildings"]:
        return False
    if "min_labs" in cond and save.buildings.laboratory < cond["min_labs"]:
        return False
    if "min_cafeteria" in cond and save.buildings.cafeteria < cond["min_cafeteria"]:
        return False
    if "min_education_power" in cond and compute_education_power(save) < cond["min_education_power"]:
        return False
    if "min_reputation" in cond and _total_reputation(save) < cond["min_reputation"]:
        return False
    if "min_students" in cond and save.students.enrolled < cond["min_students"]:
        return False
    return True


def _leading_field(save: SaveState) -> str:
    fields = [
        ("arts", save.reputation.arts),
        ("engineering", save.reputation.engineering),
        ("medical", save.reputation.medical),
        ("humanities", save.reputation.humanities),
    ]
    return max(fields, key=lambda x: x[1])[0]


def pick_event(save: SaveState) -> EventDefinition | None:
    if random.random() >= 0.25:
        return None
    candidates = [e for e in _EVENT_LIST if _check_conditions(e, save)]
    if not candidates:
        return None
    return random.choices(candidates, weights=[e.weight for e in candidates], k=1)[0]


def _apply_effects(save: SaveState, effects: dict[str, int]) -> list[str]:
    logs: list[str] = []
    for key, value in effects.items():
        if key == "budget":
            save.budget = max(0, save.budget + value)
            logs.append(f"예산 {value:+}G")
        elif key == "bonus_freshmen":
            save.bonus_freshmen += value
            logs.append(f"다음 입학 시 지원자 +{value}명")
        elif key == "reputation_leading":
            field = _leading_field(save)
            field_label = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}[field]
            current = getattr(save.reputation, field)
            setattr(save.reputation, field, max(0, current + value))
            logs.append(f"{field_label} 명성 {value:+}")
        elif key == "reputation_each":
            for f in ("arts", "engineering", "medical", "humanities"):
                current = getattr(save.reputation, f)
                setattr(save.reputation, f, max(0, current + value))
            logs.append(f"전체 명성 각 {value:+}")
        elif key.startswith("reputation_"):
            field = key.replace("reputation_", "")
            if hasattr(save.reputation, field):
                current = getattr(save.reputation, field)
                setattr(save.reputation, field, max(0, current + value))
                field_label = {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}.get(field, field)
                logs.append(f"{field_label} 명성 {value:+}")
    return logs


def apply_event(save: SaveState, event: EventDefinition, choice: str | None = None) -> list[str]:
    if choice == "b" and event.choice_b_effects is not None:
        effects = event.choice_b_effects
    else:
        effects = event.effects

    header = f"🎲 {event.name}"
    detail_logs = _apply_effects(save, effects)
    return [header, *detail_logs] if detail_logs else [header, "변화 없음"]
```

- [ ] **Step 2: Create test_events.py**

```python
# chatbot-server/tests/test_events.py
from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from app.models.schemas import (
    AdmissionCriteria, BuildingState, ReputationState, SaveState, StudentState,
)
from app.services.events import (
    EVENTS, apply_event, compute_education_power, pick_event,
)


def _make_save(**overrides) -> SaveState:
    defaults = dict(
        userId="test", year=1, month=1, budget=480,
        reputation=ReputationState(arts=6, engineering=6, medical=6, humanities=12),
        students=StudentState(enrolled=72, averageLevel=5.0),
        admissionPolicy="normal",
        admissionCriteria=AdmissionCriteria(math=5, science=5, english=5, korean=5),
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0),
        departments=["humanities"], logs=[],
    )
    defaults.update(overrides)
    return SaveState.model_validate(defaults)


def test_compute_education_power():
    save = _make_save(departments=["humanities", "computer"])
    # classroom=1 -> 8, cafeteria=0 -> 0, humanities=4, computer=5 -> 17
    assert compute_education_power(save) == 17


def test_pick_event_returns_none_when_probability_fails():
    save = _make_save(year=5, departments=["humanities", "computer"])
    random.seed(0)
    # Run multiple times; at least some should return None
    results = [pick_event(save) for _ in range(20)]
    assert None in results


def test_pick_event_returns_none_when_candidates_empty():
    # Initial state: only 1 department, no labs, no cafeteria -> very few events qualify
    # Force probability to pass but no candidates
    save = _make_save(year=1, departments=[], buildings=BuildingState(classroom=0, dormitory=0, laboratory=0, cafeteria=0))
    with patch("app.services.events.random.random", return_value=0.1):
        result = pick_event(save)
    assert result is None


def test_pick_event_respects_conditions():
    save = _make_save(year=3, departments=["humanities", "computer"],
                      buildings=BuildingState(classroom=2, dormitory=1, laboratory=1, cafeteria=1))
    with patch("app.services.events.random.random", return_value=0.1):
        result = pick_event(save)
    assert result is not None


def test_apply_positive_event_changes_budget():
    save = _make_save(budget=100)
    event = EVENTS["corp_collab"]
    logs = apply_event(save, event)
    assert save.budget == 180
    assert any("예산" in l for l in logs)


def test_apply_negative_event_floors_at_zero():
    save = _make_save(budget=30)
    event = EVENTS["building_repair"]  # budget -60
    apply_event(save, event)
    assert save.budget == 0


def test_apply_event_reputation_leading():
    save = _make_save(reputation=ReputationState(arts=50, engineering=10, medical=10, humanities=10))
    event = EVENTS["paper_viral"]  # reputation_leading +8
    apply_event(save, event)
    assert save.reputation.arts == 58  # arts is leading


def test_apply_event_reputation_each():
    save = _make_save(reputation=ReputationState(arts=10, engineering=10, medical=10, humanities=10))
    event = EVENTS["edu_award"]  # reputation_each +2
    apply_event(save, event)
    assert save.reputation.arts == 12
    assert save.reputation.engineering == 12
    assert save.reputation.medical == 12
    assert save.reputation.humanities == 12


def test_apply_choice_event_a():
    save = _make_save(budget=100)
    event = EVENTS["big_donation"]  # choice A: budget +200
    apply_event(save, event, choice="a")
    assert save.budget == 300


def test_apply_choice_event_b():
    save = _make_save(reputation=ReputationState(arts=10, engineering=10, medical=10, humanities=10))
    event = EVENTS["big_donation"]  # choice B: reputation_each +4
    apply_event(save, event, choice="b")
    assert save.reputation.arts == 14
    assert save.reputation.engineering == 14


def test_apply_bonus_freshmen():
    save = _make_save()
    event = EVENTS["applicant_surge"]  # bonus_freshmen +15
    apply_event(save, event)
    assert save.bonus_freshmen == 15
```

- [ ] **Step 3: Run tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/test_events.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add chatbot-server/app/services/events.py chatbot-server/tests/test_events.py
git commit -m "feat: add events module with definitions, pick_event, and apply_event"
```

---

### Task 3: Integrate Events into GameEngine

**Files:**
- Modify: `chatbot-server/app/services/game_engine.py`
- Modify: `chatbot-server/tests/test_game_engine.py`

- [ ] **Step 1: Update _education_power to use compute_education_power**

In `game_engine.py`, replace `_education_power` method body:

```python
def _education_power(self, save: SaveState) -> int:
    from app.services.events import compute_education_power
    return compute_education_power(save)
```

- [ ] **Step 2: Update advance_turn with event integration**

At the top of `game_engine.py`, add import:
```python
from app.services.events import EVENTS, apply_event, pick_event
```

In `advance_turn`, add pending event expiration at the start (before budget calculation):
```python
async def advance_turn(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
    save = await self._get_or_create(request.user.id, repo)

    # Expire unanswered choice event
    if save.pending_event is not None:
        expired = EVENTS.get(save.pending_event)
        if expired:
            save.logs = [f"⏰ '{expired.name}' 이벤트에 응답하지 않아 기회가 사라졌습니다.", *save.logs][:5]
        save.pending_event = None

    # ... existing budget/month/graduation/admission code ...
```

After the admission/graduation block and before `save.logs = [...]`, add event judgment:
```python
    # Event judgment
    event = pick_event(save)
    if event is not None:
        if event.event_type in ("positive", "negative"):
            event_logs = apply_event(save, event)
            logs.extend(event_logs)
        elif event.event_type == "choice":
            save.pending_event = event.id
            logs.append(f"📢 {event.name}: {event.description}")
```

Before the return, adjust quickReplies if there's a pending choice:
```python
    quick_replies = ["다음 달 진행", "건물 건설", "학과 개설", "내 대학 현황"]
    if save.pending_event is not None:
        quick_replies = ["선택 A", "선택 B", "내 대학 현황"]
```

- [ ] **Step 3: Update _apply_admission to use bonus_freshmen**

In `_apply_admission`, change the freshmen calculation:
```python
freshmen = max(20, 110 - difficulty_penalty + round(dorm_capacity * 0.35) + save.bonus_freshmen)
save.bonus_freshmen = 0  # Reset after use
```

- [ ] **Step 4: Add event_choice method to GameEngine**

```python
async def event_choice(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
    save = await self._get_or_create(request.user.id, repo)
    if save.pending_event is None:
        return self._error("진행 중인 이벤트가 없습니다.", "NO_PENDING_EVENT")

    event = EVENTS.get(save.pending_event)
    if event is None:
        save.pending_event = None
        await repo.put(request.user.id, save)
        return self._error("알 수 없는 이벤트입니다.", "UNKNOWN_EVENT")

    choice = request.action.params.get("choice", "a")
    choice_label = event.choice_a_label if choice == "a" else event.choice_b_label
    event_logs = apply_event(save, event, choice=choice)
    save.pending_event = None
    save.logs = [*event_logs, *save.logs][:5]
    await repo.put(request.user.id, save)

    return GameResult(
        message=f"'{event.name}' — {choice_label}을 선택했습니다.",
        logs=event_logs,
        quickReplies=["다음 달 진행", "건물 건설", "학과 개설", "내 대학 현황"],
        save=save,
    )
```

- [ ] **Step 5: Add event-related tests to test_game_engine.py**

Append to `chatbot-server/tests/test_game_engine.py`:

```python
from unittest.mock import patch
from app.services.events import EVENTS

async def test_advance_turn_can_trigger_event(engine, repo, user_key):
    save = make_save(user_key, year=3, departments=["humanities", "computer"],
                     budget=500)
    save.buildings.laboratory = 1
    save.buildings.cafeteria = 1
    await repo.put(user_key, save)

    # Force event to trigger (probability passes) and pick corp_collab
    with patch("app.services.events.random.random", return_value=0.1), \
         patch("app.services.events.random.choices", return_value=[EVENTS["corp_collab"]]):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert any("산학협력" in l for l in result.logs)


async def test_choice_event_sets_pending(engine, repo, user_key):
    save = make_save(user_key, year=3, departments=["humanities", "computer"],
                     budget=500)
    save.buildings.laboratory = 1
    await repo.put(user_key, save)

    with patch("app.services.events.random.random", return_value=0.1), \
         patch("app.services.events.random.choices", return_value=[EVENTS["big_donation"]]):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert result.save.pending_event == "big_donation"
    assert "선택 A" in result.quick_replies


async def test_pending_event_expires_on_next_turn(engine, repo, user_key):
    save = make_save(user_key, year=3)
    save.pending_event = "big_donation"
    await repo.put(user_key, save)

    with patch("app.services.events.pick_event", return_value=None):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert result.save.pending_event is None
    assert any("기회가 사라졌습니다" in l for l in result.save.logs)


async def test_event_choice_clears_pending(engine, repo, user_key):
    save = make_save(user_key)
    save.pending_event = "big_donation"
    await repo.put(user_key, save)

    webhook = make_webhook(user_key, action_name="EVENT_CHOICE", choice="a")
    result = await engine.event_choice(webhook, repo)
    assert result.ok is True
    assert result.save.pending_event is None
    assert result.save.budget > save.budget  # +200G


async def test_bonus_freshmen_applied_in_march(engine, repo, user_key):
    save = make_save(user_key, month=2)
    save.bonus_freshmen = 15
    await repo.put(user_key, save)

    with patch("app.services.events.pick_event", return_value=None):
        result = await engine.advance_turn(make_webhook(user_key), repo)

    assert result.save.month == 3
    assert result.save.bonus_freshmen == 0  # Reset after use
```

- [ ] **Step 6: Update conftest.py make_save to support new fields**

In `chatbot-server/tests/conftest.py`, update `make_save` to accept `pending_event` and `bonus_freshmen` if not already supported. Add to the keyword args and the dict passed to `model_validate`:

```python
pending_event: str | None = None,
bonus_freshmen: int = 0,
```

And in the dict:
```python
"pendingEvent": pending_event,
"bonusFreshmen": bonus_freshmen,
```

- [ ] **Step 7: Run all tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/ -v`
Expected: All PASS (17 existing + 5 new = 22+)

- [ ] **Step 8: Commit**

```bash
git add chatbot-server/app/services/game_engine.py chatbot-server/tests/test_game_engine.py chatbot-server/tests/conftest.py
git commit -m "feat: integrate random events into advance_turn and add event_choice"
```

---

### Task 4: API Endpoint + Integration Tests

**Files:**
- Modify: `chatbot-server/app/api/routes/kakao.py`
- Modify: `chatbot-server/tests/test_api.py`

- [ ] **Step 1: Add event-choice route**

In `chatbot-server/app/api/routes/kakao.py`, add:

```python
@router.post("/event-choice")
async def event_choice(request: KakaoWebhookRequest, repo: SaveRepository = Depends(get_repository)) -> dict:
    result = await game_engine.event_choice(request, repo)
    return to_kakao_response(result)
```

- [ ] **Step 2: Add API integration tests**

Append to `chatbot-server/tests/test_api.py`:

```python
from unittest.mock import patch
from app.services.events import EVENTS

async def test_event_choice_endpoint_no_pending(client):
    user_key = "event_test_no_pending"
    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))
    resp = await client.post(
        "/webhooks/kakao/event-choice",
        json=_action_payload(user_key, "EVENT_CHOICE"),
    )
    assert resp.status_code == 200
    body = resp.json()
    # Should get error response since no pending event
    text = body["template"]["outputs"][0]["simpleText"]["text"]
    assert "진행 중인 이벤트가 없습니다" in text


async def test_event_choice_endpoint_success(client):
    user_key = "event_test_success"
    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))

    # Manually set pending_event via advance_turn with mocked event
    from app.repositories.in_memory import save_repository
    save = await save_repository.get(user_key)
    save.pending_event = "big_donation"
    await save_repository.put(user_key, save)

    payload = _payload(user_key)
    payload["action"] = {"name": "EVENT_CHOICE", "params": {"choice": "a"}}
    resp = await client.post("/webhooks/kakao/event-choice", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    text = body["template"]["outputs"][0]["simpleText"]["text"]
    assert "수락" in text
```

- [ ] **Step 3: Run all tests**

Run: `cd chatbot-server && .venv/bin/python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add chatbot-server/app/api/routes/kakao.py chatbot-server/tests/test_api.py
git commit -m "feat: add event-choice API endpoint with integration tests"
```
