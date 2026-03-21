from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
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
    # Positive events
    EventDefinition(
        id="corp_collab",
        name="산학협력",
        description="지역 기업과 산학협력 협약을 체결했습니다. 예산이 증가합니다.",
        event_type="positive",
        effects={"budget": 80},
        conditions={"min_departments": 2},
        weight=10,
    ),
    EventDefinition(
        id="alumni_donation",
        name="동문 기부",
        description="졸업생이 대학 발전을 위해 기부했습니다.",
        event_type="positive",
        effects={"budget": 150},
        conditions={"min_year": 2},
        weight=8,
    ),
    EventDefinition(
        id="paper_viral",
        name="논문 화제",
        description="연구소의 논문이 화제가 되었습니다. 선도 분야 명성이 상승합니다.",
        event_type="positive",
        effects={"reputation_leading": 8},
        conditions={"min_labs": 1},
        weight=10,
    ),
    EventDefinition(
        id="local_festival",
        name="지역 축제",
        description="지역 축제 참가로 예체능 명성이 올랐습니다.",
        event_type="positive",
        effects={"reputation_arts": 5},
        conditions={"min_cafeteria": 1},
        weight=8,
    ),
    EventDefinition(
        id="edu_award",
        name="교육 우수상",
        description="교육 우수 대학으로 선정되어 전 분야 명성이 상승합니다.",
        event_type="positive",
        effects={"reputation_each": 2},
        conditions={"min_education_power": 30, "min_year": 2},
        weight=7,
    ),
    EventDefinition(
        id="applicant_surge",
        name="지원자 급증",
        description="대학 명성이 높아져 입학 지원자가 급증했습니다.",
        event_type="positive",
        effects={"bonus_freshmen": 15},
        conditions={"min_reputation": 50},
        weight=7,
    ),
    # Negative events
    EventDefinition(
        id="building_repair",
        name="건물 수리",
        description="노후 건물 수리 비용이 발생했습니다.",
        event_type="negative",
        effects={"budget": -60},
        conditions={"min_buildings": 4},
        weight=6,
    ),
    EventDefinition(
        id="prof_departure",
        name="교수 이탈",
        description="핵심 교수가 타 대학으로 이직했습니다. 선도 분야 명성이 하락합니다.",
        event_type="negative",
        effects={"reputation_leading": -5},
        conditions={"min_departments": 2},
        weight=5,
    ),
    EventDefinition(
        id="tuition_protest",
        name="등록금 시위",
        description="학생들이 등록금 인상에 항의했습니다. 예산이 감소합니다.",
        event_type="negative",
        effects={"budget": -80},
        conditions={"min_students": 100},
        weight=4,
    ),
    EventDefinition(
        id="equipment_failure",
        name="장비 고장",
        description="연구소 장비가 고장났습니다. 수리 비용이 발생합니다.",
        event_type="negative",
        effects={"budget": -40},
        conditions={"min_labs": 1},
        weight=5,
    ),
    # Choice events
    EventDefinition(
        id="big_donation",
        name="대규모 기부",
        description="대규모 기부 제안이 들어왔습니다. 즉시 예산을 받거나 명성을 선택하세요.",
        event_type="choice",
        effects={"budget": 200},
        conditions={"min_year": 3},
        weight=3,
        choice_b_effects={"reputation_each": 4},
        choice_a_label="예산 +200G 수령",
        choice_b_label="전 분야 명성 +4",
    ),
    EventDefinition(
        id="star_prof",
        name="스타 교수 초빙",
        description="유명 교수 초빙 제안이 왔습니다. 비용을 들여 명성을 높이겠습니까?",
        event_type="choice",
        effects={"budget": -100, "reputation_leading": 10},
        conditions={"min_labs": 1},
        weight=3,
        choice_b_effects={},
        choice_a_label="초빙 수락 (예산 -100G, 선도 명성 +10)",
        choice_b_label="거절",
    ),
    EventDefinition(
        id="club_support",
        name="동아리 지원",
        description="예체능 동아리 지원 요청이 왔습니다. 지원하겠습니까?",
        event_type="choice",
        effects={"budget": -50, "reputation_arts": 8},
        conditions={"min_students": 80},
        weight=3,
        choice_b_effects={},
        choice_a_label="지원 수락 (예산 -50G, 예체능 명성 +8)",
        choice_b_label="거절",
    ),
]

EVENTS: dict[str, EventDefinition] = {e.id: e for e in _EVENT_LIST}


def compute_education_power(save: SaveState) -> int:
    """Compute the university's education power from buildings and departments.

    Args:
        save: Current game save state.

    Returns:
        Education power as an integer.
    """
    # Lazy import to avoid circular dependency with game_engine
    from app.services.game_engine import DEPARTMENTS
    dept_boost = sum(DEPARTMENTS[d].education_boost for d in save.departments)
    return save.buildings.classroom * 8 + save.buildings.cafeteria * 2 + dept_boost


def _total_buildings(save: SaveState) -> int:
    """Sum all building counts across all building types."""
    b = save.buildings
    return b.classroom + b.dormitory + b.laboratory + b.cafeteria


def _total_reputation(save: SaveState) -> int:
    """Sum all reputation field values."""
    r = save.reputation
    return r.arts + r.engineering + r.medical + r.humanities


def _check_conditions(event: EventDefinition, save: SaveState) -> bool:
    """Check whether all event conditions are satisfied by the save state.

    Args:
        event: The event whose conditions to check.
        save: Current game save state.

    Returns:
        True if all conditions are met, False otherwise.
    """
    for key, threshold in event.conditions.items():
        if key == "min_year":
            if save.year < threshold:
                return False
        elif key == "min_departments":
            if len(save.departments) < threshold:
                return False
        elif key == "min_labs":
            if save.buildings.laboratory < threshold:
                return False
        elif key == "min_cafeteria":
            if save.buildings.cafeteria < threshold:
                return False
        elif key == "min_buildings":
            if _total_buildings(save) < threshold:
                return False
        elif key == "min_students":
            if save.students.enrolled < threshold:
                return False
        elif key == "min_reputation":
            if _total_reputation(save) < threshold:
                return False
        elif key == "min_education_power":
            if compute_education_power(save) < threshold:
                return False
    return True


def _leading_field(save: SaveState) -> str:
    """Return the reputation field name with the highest value.

    Args:
        save: Current game save state.

    Returns:
        Field name string: one of 'arts', 'engineering', 'medical', 'humanities'.
    """
    fields = [
        ("arts", save.reputation.arts),
        ("engineering", save.reputation.engineering),
        ("medical", save.reputation.medical),
        ("humanities", save.reputation.humanities),
    ]
    return max(fields, key=lambda x: x[1])[0]


def pick_event(save: SaveState) -> EventDefinition | None:
    """Potentially pick a random event based on conditions and probability.

    There is a 25% chance an event fires each call. If no eligible events
    exist, returns None.

    Args:
        save: Current game save state.

    Returns:
        An EventDefinition if one is selected, or None.
    """
    if random.random() >= 0.25:
        return None

    candidates = [e for e in _EVENT_LIST if _check_conditions(e, save)]
    if not candidates:
        return None

    weights = [e.weight for e in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def _apply_effects(save: SaveState, effects: dict[str, int]) -> list[str]:
    """Apply an effects dictionary to the save state and return log messages.

    Args:
        save: Current game save state (mutated in place).
        effects: Mapping of effect keys to integer values.

    Returns:
        List of human-readable log strings describing applied effects.
    """
    logs: list[str] = []

    for key, value in effects.items():
        if key == "budget":
            save.budget = max(0, save.budget + value)
            logs.append(f"예산 {value:+}G")
        elif key == "bonus_freshmen":
            save.bonus_freshmen += value
            logs.append(f"입학 지원자 보너스 +{value}명")
        elif key == "reputation_leading":
            field = _leading_field(save)
            current = getattr(save.reputation, field)
            setattr(save.reputation, field, max(0, current + value))
            logs.append(f"선도 분야({field}) 명성 {value:+}")
        elif key == "reputation_each":
            for field in ("arts", "engineering", "medical", "humanities"):
                current = getattr(save.reputation, field)
                setattr(save.reputation, field, max(0, current + value))
            logs.append(f"전 분야 명성 {value:+}")
        elif key.startswith("reputation_"):
            field = key[len("reputation_"):]
            current = getattr(save.reputation, field)
            setattr(save.reputation, field, max(0, current + value))
            logs.append(f"{field} 명성 {value:+}")

    return logs


def apply_event(
    save: SaveState,
    event: EventDefinition,
    choice: Literal["a", "b"] | None = None,
) -> list[str]:
    """Apply an event's effects to the save state.

    For choice events, 'a' applies primary effects and 'b' applies
    choice_b_effects. Non-choice events always apply primary effects.

    Args:
        save: Current game save state (mutated in place).
        event: The event to apply.
        choice: 'a' or 'b' for choice events; None for automatic events.

    Returns:
        List of log strings describing the applied effects.
    """
    if event.event_type == "choice" and choice == "b":
        effects = event.choice_b_effects or {}
    else:
        effects = event.effects

    return _apply_effects(save, effects)
