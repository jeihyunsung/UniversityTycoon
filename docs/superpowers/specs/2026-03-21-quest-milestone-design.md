# Quest & Milestone System Design

## Goal

초반 유저에게 순차적 마일스톤으로 게임 가이드를 제공하고, 1년차 이후 플레이 스타일에 따라 특화 분기 퀘스트를 해금하여 장기적인 목표와 진행감을 부여한다.

## Architecture

퀘스트 로직을 `quests.py` 독립 모듈로 분리한다. 마일스톤은 순차적으로 진행되며, 특화 퀘스트는 상위 2개 명성 분야만 활성화된다. advance_turn과 build/department/admission 액션 후에 달성 여부를 체크하고 보상을 적용한다.

## Milestone System (1년차 가이드)

순차적 — 이전 마일스톤을 달성해야 다음이 활성화된다.

| # | ID | 이름 | 달성 조건 | 보상 |
|---|-----|------|----------|------|
| 1 | `first_step` | 첫 걸음 | 게임 시작 (자동 완료) | 칭호: "신생 대학" |
| 2 | `campus_expand` | 캠퍼스 확장 | 건물 총 3개 이상 | budget +50 |
| 3 | `study_begins` | 학문의 시작 | 학과 2개 이상 | budget +30, reputation_leading +3 |
| 4 | `admission_strategist` | 입학 전략가 | admission_changed == True | budget +30 |
| 5 | `first_graduation` | 첫 졸업식 | year 2 이상 (졸업 경험) | budget +80, 칭호: "교육자" |
| 6 | `growing_campus` | 성장하는 캠퍼스 | 건물 총 5개 이상 | budget +60 |
| 7 | `dept_diversity` | 학과 다양화 | 학과 3개 이상 | budget +100, 칭호: "종합 대학" |
| 8 | `first_anniversary` | 1주년 | year 2 이상 + 마일스톤 1~7 모두 완료 | 칭호: "1주년 대학", 특화 퀘스트 해금 |

### 마일스톤 조건 체크 방법

조건은 SaveState 필드로 직접 확인:
- 건물 수: `_total_buildings(save)` (events.py에서 import)
- 학과 수: `len(save.departments)`
- 입학 정책 변경 여부: `save.admission_changed` (bool 플래그)
- 연차: `save.year >= N`
- 이전 마일스톤: `prerequisite in save.completed_milestones`

마일스톤 4 "입학 전략가"는 `admission_changed: bool` 플래그로 체크한다. admission 메서드에서 정책 변경 시 `save.admission_changed = True`로 설정. 다시 normal로 돌려도 플래그는 유지된다.

### 다중 마일스톤 동시 달성

`check_and_apply`는 한 번 호출 시 여러 마일스톤을 연쇄 달성할 수 있다. 루프 내에서 `completed_milestones`에 추가하면서 다음 마일스톤의 prerequisite를 즉시 충족시킨다.

### start_game에서의 초기화

`_initial_save`에서 `completed_milestones=["first_step"]`, `title="신생 대학"`으로 사전 설정한다. 마일스톤 1은 게임 시작 시 자동 완료 상태.

## Specialization Quest System (1년차 이후)

마일스톤 8 달성 시 상위 2개 명성 분야의 퀘스트 라인이 `active_quest_lines`에 추가된다. 각 분야는 3단계 순차 퀘스트.

### arts 퀘스트 라인

| 단계 | ID | 이름 | 달성 조건 | 보상 |
|------|-----|------|----------|------|
| 1 | `arts_1` | 예술의 꽃 | arts 명성 20+ | budget +60, 칭호: "예술 대학" |
| 2 | `arts_2` | 축제의 대학 | 식당 2개 + arts 명성 35+ | budget +120, reputation_arts +5 |
| 3 | `arts_3` | 예술 명문 | arts 명성 60+ | budget +200, 칭호: "예술 명문대" |

### engineering 퀘스트 라인

| 단계 | ID | 이름 | 달성 조건 | 보상 |
|------|-----|------|----------|------|
| 1 | `eng_1` | 기술의 요람 | engineering 명성 20+ | budget +60, 칭호: "공학 대학" |
| 2 | `eng_2` | 산학협력 선도 | 연구소 2개 + engineering 명성 35+ | budget +120, reputation_engineering +5 |
| 3 | `eng_3` | 공학 명문 | engineering 명성 60+ | budget +200, 칭호: "공학 명문대" |

### medical 퀘스트 라인

| 단계 | ID | 이름 | 달성 조건 | 보상 |
|------|-----|------|----------|------|
| 1 | `med_1` | 생명의 학교 | medical 명성 20+ | budget +60, 칭호: "의학 대학" |
| 2 | `med_2` | 연구 중심 병원 | 연구소 2개 + medical 명성 35+ | budget +120, reputation_medical +5 |
| 3 | `med_3` | 의학 명문 | medical 명성 60+ | budget +200, 칭호: "의학 명문대" |

### humanities 퀘스트 라인

| 단계 | ID | 이름 | 달성 조건 | 보상 |
|------|-----|------|----------|------|
| 1 | `hum_1` | 지성의 전당 | humanities 명성 20+ | budget +60, 칭호: "인문학 대학" |
| 2 | `hum_2` | 학술 도시 | 강의실 3개 + humanities 명성 35+ | budget +120, reputation_humanities +5 |
| 3 | `hum_3` | 인문 명문 | humanities 명성 60+ | budget +200, 칭호: "인문 명문대" |

### 퀘스트 활성화 규칙

- 마일스톤 8 달성 시 `_leading_two_fields(save)` → 상위 2개 분야 → `active_quest_lines`에 추가
- 각 라인의 1단계부터 순차 진행 (1→2→3)
- 이미 완료된 퀘스트는 `completed_quests`에 기록

## Data Model

### QuestDefinition (dataclass, frozen)

```python
@dataclass(frozen=True)
class QuestDefinition:
    id: str
    name: str
    description: str
    quest_type: Literal["milestone", "specialization"]
    field: str | None           # None for milestones, "arts"/"engineering" etc for specialization
    conditions: dict[str, int]  # {"min_buildings": 3, "min_departments": 2}
    rewards: dict[str, int | str]  # {"budget": 50, "title": "신생 대학", "reputation_leading": 3}
    prerequisite: str | None    # previous quest/milestone ID that must be completed first
```

### SaveState 변경

```python
completed_milestones: list[str] = Field(default_factory=list, alias="completedMilestones")
active_quest_lines: list[str] = Field(default_factory=list, alias="activeQuestLines")
completed_quests: list[str] = Field(default_factory=list, alias="completedQuests")
title: str = Field(default="신생 대학", alias="title")
admission_changed: bool = Field(default=False, alias="admissionChanged")
```

### DB 변경

`GameSaveRow`에 5개 컬럼 추가:
- `completed_milestones: Mapped[list] = mapped_column(JSON, default=list)`
- `active_quest_lines: Mapped[list] = mapped_column(JSON, default=list)`
- `completed_quests: Mapped[list] = mapped_column(JSON, default=list)`
- `title: Mapped[str] = mapped_column(String(64), default="신생 대학")`
- `admission_changed: Mapped[bool] = mapped_column(default=False)`

`PostgresSaveRepository`에 직렬화/역직렬화 추가.

## Module: quests.py

공유 헬퍼 함수 (`_total_buildings`, `_total_reputation`, `_leading_field`)는 `events.py`에서 import한다. 중복 구현하지 않는다.

### check_and_apply(save: SaveState) -> list[str]

메인 진입점. 마일스톤과 퀘스트를 한 번에 체크하고 보상을 적용한다.

1. `_check_milestones(save)` → 달성된 마일스톤 리스트
2. 마일스톤 8 달성 시 → `_activate_quest_lines(save)`
3. `_check_quests(save)` → 달성된 퀘스트 리스트
4. 각 달성 항목에 대해 `_apply_reward(save, quest.rewards)`
5. 로그 메시지 리스트 반환

### _check_milestones(save) -> list[QuestDefinition]

순차 체크:
1. `completed_milestones`에 없는 마일스톤만 대상
2. `prerequisite`가 있으면 그것이 `completed_milestones`에 있는지 확인
3. 조건 체크 (건물 수, 학과 수, 연차 등)
4. 달성 시 `save.completed_milestones.append(quest.id)`

### _check_quests(save) -> list[QuestDefinition]

활성 퀘스트 라인만 체크:
1. `active_quest_lines`에 있는 분야만 대상
2. 해당 분야의 다음 미완료 단계 찾기
3. `prerequisite` 확인 (이전 단계 완료 여부)
4. 조건 체크
5. 달성 시 `save.completed_quests.append(quest.id)`

### _activate_quest_lines(save)

상위 2개 명성 분야를 `active_quest_lines`에 추가. 이미 활성화되어 있으면 무시:
```python
def _activate_quest_lines(save: SaveState) -> None:
    if save.active_quest_lines:
        return  # 이미 활성화됨
    fields = sorted(
        [("arts", save.reputation.arts), ("engineering", save.reputation.engineering),
         ("medical", save.reputation.medical), ("humanities", save.reputation.humanities)],
        key=lambda x: x[1], reverse=True
    )
    save.active_quest_lines = [f[0] for f in fields[:2]]
```

### _apply_reward(save, rewards)

```python
for key, value in rewards.items():
    if key == "budget":
        save.budget += value
    elif key == "title":
        save.title = value
    elif key.startswith("reputation_"):
        # reputation_leading, reputation_arts 등 — events.py와 동일 패턴
```

### get_quest_summary(save) -> str

현재 진행 중인 퀘스트 1줄 요약 (load_status에 사용):
- 마일스톤 진행 중이면: "📋 다음 목표: 캠퍼스 확장 (건물 2/3개)"
- 특화 퀘스트 진행 중이면: "📋 다음 목표: 예술의 꽃 (arts 명성 15/20)"
- 모두 완료면: "🎓 모든 퀘스트 완료!"

### get_quest_list(save) -> list[dict]

전체 퀘스트 목록 (quests 엔드포인트에 사용):
- 마일스톤: 완료/진행중/잠금 상태
- 특화 퀘스트: 활성 라인만 표시, 완료/진행중/잠금 상태

## Integration Points

### advance_turn
턴 종료 시 (이벤트 판정 이후):
```python
quest_logs = check_and_apply(save)
if quest_logs:
    logs.extend(quest_logs)
```

### build / department / admission
액션 처리 후, 저장 전:
```python
quest_logs = check_and_apply(save)
if quest_logs:
    save.logs = [*quest_logs, *save.logs][:5]
```

### load_status
메시지에 퀘스트 요약 추가:
```python
quest_summary = get_quest_summary(save)
message = f"... / {quest_summary}"
```

### 새 엔드포인트: POST /webhooks/kakao/quests
퀘스트 전체 목록과 진행률 조회.

### quickReplies 변경
상태 조회의 quickReplies에 "퀘스트" 추가:
```python
quickReplies=["다음 달 진행", "건물 건설", "학과 개설", "입학 정책", "퀘스트", "지난 결과 보기"]
```

## File Structure

```
chatbot-server/app/
  services/
    quests.py              # CREATE: QuestDefinition, MILESTONES, QUESTS, check_and_apply, get_quest_summary, get_quest_list
    game_engine.py         # MODIFY: advance_turn/build/department/admission에 퀘스트 체크, load_status에 요약, quests 메서드
  models/
    schemas.py             # MODIFY: SaveState에 4개 필드 추가
    db_models.py           # MODIFY: GameSaveRow에 4개 컬럼 추가
  repositories/
    postgres.py            # MODIFY: 직렬화/역직렬화
  api/
    routes/kakao.py        # MODIFY: quests 엔드포인트 추가
tests/
  test_quests.py           # CREATE: 퀘스트 로직 단위 테스트
```

## Testing

### test_quests.py

- `test_first_step_auto_completed`: 게임 시작 시 첫 마일스톤 자동 완료, 칭호 "신생 대학"
- `test_campus_expand_milestone`: 건물 3개 → 마일스톤 달성, budget +50
- `test_milestone_requires_prerequisite`: 이전 마일스톤 미완료 시 다음 마일스톤 미달성
- `test_first_anniversary_activates_quest_lines`: 마일스톤 8 달성 → active_quest_lines 2개 추가
- `test_quest_line_top_two_fields`: 명성 arts=50, eng=40, med=10, hum=10 → arts, engineering 활성
- `test_specialization_quest_sequential`: 1단계 완료 전 2단계 미달성
- `test_specialization_quest_applies_reward`: arts_1 달성 → budget +60, 칭호 "예술 대학"
- `test_get_quest_summary_milestone`: 진행 중 마일스톤 요약 문자열 확인
- `test_get_quest_summary_specialization`: 진행 중 특화 퀘스트 요약 확인
- `test_get_quest_list`: 전체 목록 구조 확인

### game_engine 테스트

- `test_advance_turn_triggers_milestone`: 턴 진행 시 마일스톤 달성 로그
- `test_build_triggers_milestone`: 건물 건설 후 마일스톤 달성
- `test_load_status_includes_quest_summary`: 상태 조회 메시지에 퀘스트 요약 포함

### API 테스트

- `test_quests_endpoint`: /webhooks/kakao/quests 응답 형식 확인

## Kakao Open Builder 추가 설정

| 블록 이름 | 패턴 발화 | 스킬 |
|-----------|----------|------|
| 퀘스트 | "퀘스트" | 퀘스트 조회 |

스킬 URL: `/webhooks/kakao/quests`
