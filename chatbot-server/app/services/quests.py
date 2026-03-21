from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models.schemas import SaveState
from app.services.events import (
    compute_education_power,
    leading_field,
    total_buildings,
    total_reputation,
)


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
    """Check all quests/milestones and apply any that are now completed.

    Args:
        save: Current game save state (mutated in place).

    Returns:
        List of log strings describing completed quests and applied rewards.
    """
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
    """Return a one-line summary of the next quest objective.

    Args:
        save: Current game save state.

    Returns:
        A single line describing the next milestone or specialization quest,
        or a completion message if all quests are done.
    """
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
    """Return the full quest list with statuses for the /quests endpoint.

    Args:
        save: Current game save state.

    Returns:
        List of dicts with 'section' headers and 'name'/'status' entries.
    """
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
