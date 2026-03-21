# Random Events System Design

## Goal

매 턴 진행 시 확률적으로 이벤트를 발생시켜 게임에 예측 불가능한 재미를 추가한다. 플레이어의 대학 상태에 따라 다른 이벤트가 발생하며, 일부 이벤트는 선택지를 제공한다.

## Architecture

이벤트 로직을 `events.py` 독립 모듈로 분리한다. `game_engine.py`의 `advance_turn`은 예산 정산 → 졸업/입학 처리 후 이벤트 판정을 호출한다. 선택형 이벤트는 `pending_event` 필드에 저장 후 별도 엔드포인트에서 처리한다.

## Event Trigger

- **시점:** `advance_turn` 내, 졸업/입학 처리 이후
- **확률:** 매 턴 25% (4달에 평균 1회)
- **판정 순서:**
  1. 25% 확률 체크 (실패하면 이벤트 없음)
  2. 현재 SaveState 기반으로 조건 충족하는 이벤트만 필터링
  3. 가중치 기반 랜덤 선택 (1개)
  4. 긍정/부정: 즉시 적용 → 로그에 포함
  5. 선택형: `pending_event`에 저장 → 빠른 답장으로 선택지 제공

## Event Types

비율: **긍정 60% / 부정 25% / 선택형 15%** (가중치로 조절)

### Positive Events

| ID | 이름 | 효과 | 조건 | 가중치 |
|----|------|------|------|--------|
| `corp_collab` | 기업 산학협력 체결 | budget +80 | 학과 2개+ | 10 |
| `alumni_donation` | 졸업생 CEO 기부 | budget +150 | year 2+ | 8 |
| `paper_viral` | 교수 논문 화제 | 주력 분야 명성 +8 | 연구소 1개+ | 10 |
| `local_festival` | 지역 축제 개최 | arts 명성 +5 | 식당 1개+ | 8 |
| `edu_award` | 교육부 우수 평가 | 전체 명성 +6 (각 분야 +1~2) | 교육력 20+ | 7 |
| `applicant_surge` | 신입생 지원 폭증 | 다음 입학 시 freshmen +15 | 총 명성 50+ | 7 |

### Negative Events

| ID | 이름 | 효과 | 조건 | 가중치 |
|----|------|------|------|--------|
| `building_repair` | 건물 보수 필요 | budget -60 | 건물 4개+ | 6 |
| `prof_departure` | 교수 이직 | 주력 분야 명성 -5 | 학과 2개+ | 5 |
| `tuition_protest` | 등록금 동결 시위 | 이번 달 수입 0 처리 | 재학생 100명+ | 4 |
| `equipment_failure` | 연구 장비 고장 | budget -40 | 연구소 1개+ | 5 |

### Choice Events

| ID | 이름 | 선택A | 선택B | 조건 | 가중치 |
|----|------|-------|-------|------|--------|
| `big_donation` | 대기업 기부 제안 | 수락: budget +200 | 거절: 명성 +15 (전체) | year 3+ | 3 |
| `star_prof` | 유명 교수 스카우트 | 채용: budget -100, 연구력 효과로 주력 명성 +10 | 패스: 변화 없음 | 연구소 1개+ | 3 |
| `club_support` | 학생 동아리 지원 요청 | 지원: budget -50, arts 명성 +8 | 거절: 변화 없음 | 재학생 80명+ | 3 |

## Data Model

### EventDefinition (dataclass, frozen)

```python
@dataclass(frozen=True)
class EventDefinition:
    id: str
    name: str
    description: str
    event_type: Literal["positive", "negative", "choice"]
    effects: dict[str, int]        # {"budget": 80} or {"reputation_arts": 8}
    choice_b_effects: dict[str, int] | None  # choice 이벤트의 B 선택 효과
    choice_a_label: str            # "수락" 등
    choice_b_label: str            # "거절" 등
    conditions: dict[str, int]     # {"min_departments": 2, "min_year": 3}
    weight: int                    # 가중치
```

### SaveState 변경

```python
pending_event: str | None = Field(default=None, alias="pendingEvent")
```

- 선택형 이벤트 발생 시 event id 저장
- 선택 완료 또는 다음 턴 진행 시 None으로 초기화

## File Structure

```
chatbot-server/app/
  services/
    events.py               # CREATE: EventDefinition, EVENTS, pick_event(), apply_event()
    game_engine.py           # MODIFY: advance_turn에 이벤트 판정 추가
  models/
    schemas.py               # MODIFY: SaveState에 pending_event 추가
  api/
    routes/kakao.py          # MODIFY: event-choice 엔드포인트 추가
tests/
  test_events.py             # CREATE: 이벤트 로직 단위 테스트
```

## Module: events.py

### pick_event(save: SaveState) -> EventDefinition | None

1. `random.random() > 0.25` → return None (75% 확률로 이벤트 없음)
2. 조건 필터링: 각 이벤트의 conditions를 save 상태와 대조
   - `min_departments`: `len(save.departments) >= N`
   - `min_year`: `save.year >= N`
   - `min_buildings`: 총 건물 수 >= N
   - `min_labs`: `save.buildings.laboratory >= N`
   - `min_cafeteria`: `save.buildings.cafeteria >= N`
   - `min_education_power`: 교육력 >= N (GameEngine._education_power 계산 필요 → 함수 분리)
   - `min_reputation`: 총 명성 >= N
   - `min_students`: `save.students.enrolled >= N`
3. 통과한 이벤트들의 가중치 기반 `random.choices` → 1개 선택

### apply_event(save: SaveState, event: EventDefinition, choice: str | None) -> list[str]

- `choice` 파라미터: None(긍정/부정), "a" 또는 "b"(선택형)
- effects dict를 순회하며 save에 적용:
  - `budget`: `save.budget += value`
  - `reputation_arts`: `save.reputation.arts += value` (다른 분야도 동일)
  - `reputation_leading`: 주력 분야에 적용
  - `reputation_all`: 모든 분야에 균등 분배
- 로그 메시지 리스트 반환

## advance_turn Integration

```python
# 기존 코드 이후에 추가
event = pick_event(save)
if event is not None:
    if event.event_type in ("positive", "negative"):
        event_logs = apply_event(save, event, choice=None)
        logs.extend(event_logs)
    elif event.event_type == "choice":
        save.pending_event = event.id
        logs.append(f"📢 {event.name}: {event.description}")
        # quickReplies에 선택지 추가
```

선택형 이벤트 발생 시 quickReplies를 선택지로 교체:
```python
quickReplies = [event.choice_a_label, event.choice_b_label]
```

## New Endpoint: POST /webhooks/kakao/event-choice

- pending_event가 없으면 → 에러 "진행 중인 이벤트가 없습니다."
- 선택 파라미터로 "a" 또는 "b" 추출
- apply_event(save, event, choice) 호출
- pending_event = None으로 초기화
- 결과 메시지 + 기존 quickReplies 반환

## Kakao Open Builder 추가 설정

| 블록 이름 | 패턴 발화 | 스킬 | 파라미터 |
|-----------|----------|------|---------|
| 이벤트 선택A | choice_a_label 텍스트 | 이벤트 선택 | choice=a |
| 이벤트 선택B | choice_b_label 텍스트 | 이벤트 선택 | choice=b |

선택형 이벤트의 빠른 답장 텍스트가 고정되어야 오픈빌더 블록과 매칭 가능. 선택지 라벨을 "수락", "거절" 같은 고정 텍스트 대신 **"선택 A", "선택 B"** 로 통일하고, 구체적인 설명은 메시지 본문에 포함.

수정된 quickReplies:
```python
quickReplies = ["선택 A", "선택 B", "내 대학 현황"]
```

오픈빌더 블록:
- "선택 A" → event-choice, params: choice=a
- "선택 B" → event-choice, params: choice=b

## Testing

### test_events.py

- `test_pick_event_returns_none_when_no_conditions_met`: 빈 대학으로 조건 있는 이벤트가 안 뽑히는지
- `test_pick_event_respects_conditions`: 조건 충족 시 이벤트 후보에 포함되는지
- `test_apply_positive_event_changes_budget`: 긍정 이벤트 적용 후 budget 변화
- `test_apply_negative_event_reduces_reputation`: 부정 이벤트 적용 후 명성 감소
- `test_apply_choice_event_a`: 선택A 효과 적용
- `test_apply_choice_event_b`: 선택B 효과 적용
- `test_pending_event_cleared_after_choice`: 선택 후 pending_event가 None

### game_engine 테스트 수정

- `test_advance_turn_can_trigger_event`: seed 고정으로 이벤트 발생 확인
- `test_choice_event_sets_pending`: 선택형 이벤트 시 pending_event 저장 확인
