# Random Events System Design

## Goal

매 턴 진행 시 확률적으로 이벤트를 발생시켜 게임에 예측 불가능한 재미를 추가한다. 플레이어의 대학 상태에 따라 다른 이벤트가 발생하며, 일부 이벤트는 선택지를 제공한다.

## Architecture

이벤트 로직을 `events.py` 독립 모듈로 분리한다. `game_engine.py`의 `advance_turn`은 예산 정산 → 졸업/입학 처리 후 이벤트 판정을 호출한다. 선택형 이벤트는 `pending_event` 필드에 저장 후 별도 엔드포인트에서 처리한다.

## Event Trigger

- **시점:** `advance_turn` 내, 졸업/입학 처리 이후
- **확률:** 매 턴 25% (4달에 평균 1회)
- **판정 순서:**
  1. `random.random() < 0.25` 확률 체크 (실패하면 이벤트 없음)
  2. 현재 SaveState 기반으로 조건 충족하는 이벤트만 필터링
  3. 가중치 기반 `random.choices` → 1개 선택
  4. 긍정/부정: 즉시 적용 → 로그에 포함
  5. 선택형: `pending_event`에 저장 → 빠른 답장으로 선택지 제공

## Event Types

비율: **긍정 60% / 부정 25% / 선택형 15%** (가중치로 조절)

### Positive Events

| ID | 이름 | 효과 | 조건 | 가중치 |
|----|------|------|------|--------|
| `corp_collab` | 기업 산학협력 체결 | budget +80 | min_departments: 2 | 10 |
| `alumni_donation` | 졸업생 CEO 기부 | budget +150 | min_year: 2 | 8 |
| `paper_viral` | 교수 논문 화제 | reputation_leading +8 | min_labs: 1 | 10 |
| `local_festival` | 지역 축제 개최 | reputation_arts +5 | min_cafeteria: 1 | 8 |
| `edu_award` | 교육부 우수 평가 | 각 분야 명성 +2 (총 +8) | min_education_power: 30, min_year: 2 | 7 |
| `applicant_surge` | 신입생 지원 폭증 | bonus_freshmen +15 (다음 3월 입학 시 적용 후 초기화) | min_reputation: 50 | 7 |

### Negative Events

| ID | 이름 | 효과 | 조건 | 가중치 |
|----|------|------|------|--------|
| `building_repair` | 건물 보수 필요 | budget -60 (최소 0) | min_buildings: 4 | 6 |
| `prof_departure` | 교수 이직 | reputation_leading -5 (최소 0) | min_departments: 2 | 5 |
| `tuition_protest` | 등록금 동결 시위 | budget -80 (최소 0) | min_students: 100 | 4 |
| `equipment_failure` | 연구 장비 고장 | budget -40 (최소 0) | min_labs: 1 | 5 |

### Choice Events

| ID | 이름 | 선택A | 선택B | 조건 | 가중치 |
|----|------|-------|-------|------|--------|
| `big_donation` | 대기업 기부 제안 | 수락: budget +200 | 거절: 각 분야 명성 +4 (총 +16) | min_year: 3 | 3 |
| `star_prof` | 유명 교수 스카우트 | 채용: budget -100, reputation_leading +10 | 패스: 변화 없음 | min_labs: 1 | 3 |
| `club_support` | 학생 동아리 지원 요청 | 지원: budget -50, reputation_arts +8 | 거절: 변화 없음 | min_students: 80 | 3 |

## Data Model

### EventDefinition (dataclass, frozen)

```python
@dataclass(frozen=True)
class EventDefinition:
    id: str
    name: str
    description: str
    event_type: Literal["positive", "negative", "choice"]
    effects: dict[str, int]                    # {"budget": 80} or {"reputation_arts": 8}
    conditions: dict[str, int]                 # {"min_departments": 2, "min_year": 3}
    weight: int                                # 가중치
    choice_b_effects: dict[str, int] | None = None   # choice 이벤트의 B 선택 효과
    choice_a_label: str | None = None          # "수락" 등 (choice만 사용)
    choice_b_label: str | None = None          # "거절" 등 (choice만 사용)
```

Non-choice 이벤트는 choice 관련 필드가 None으로 유지된다.

### EVENTS dict

```python
EVENTS: dict[str, EventDefinition] = {event.id: event for event in [...]}
```

dict로 저장하여 `pending_event` id로 즉시 조회 가능.

### SaveState 변경

```python
pending_event: str | None = Field(default=None, alias="pendingEvent")
bonus_freshmen: int = Field(default=0, alias="bonusFreshmen")
```

- `pending_event`: 선택형 이벤트 발생 시 event id 저장. 선택 완료 시 None으로 초기화.
- `bonus_freshmen`: `applicant_surge` 이벤트 효과 저장. 3월 입학 시 적용 후 0으로 초기화.

### DB 변경 (PostgreSQL)

- `GameSaveRow`에 `pending_event: Mapped[str | None]`과 `bonus_freshmen: Mapped[int]` 컬럼 추가.
- `PostgresSaveRepository.put()`과 `_row_to_save()`에 두 필드 직렬화/역직렬화 추가.
- Alembic 마이그레이션 생성.

## Effect Application Rules

`apply_event`에서 effects dict 키 해석 규칙:

| 키 | 동작 |
|----|------|
| `budget` | `save.budget = max(0, save.budget + value)` |
| `reputation_arts` | `save.reputation.arts = max(0, save.reputation.arts + value)` |
| `reputation_engineering` | 동일 패턴 |
| `reputation_medical` | 동일 패턴 |
| `reputation_humanities` | 동일 패턴 |
| `reputation_leading` | 가장 높은 명성 분야에 적용 (max 0 보장) |
| `reputation_each` | 4개 분야 각각에 value만큼 적용 |
| `bonus_freshmen` | `save.bonus_freshmen += value` |

모든 수치는 max(0)으로 음수 방지.

## File Structure

```
chatbot-server/app/
  services/
    events.py               # CREATE: EventDefinition, EVENTS, pick_event(), apply_event(), compute_education_power()
    game_engine.py           # MODIFY: advance_turn에 이벤트 판정 추가, _apply_admission에 bonus_freshmen 반영
  models/
    schemas.py               # MODIFY: SaveState에 pending_event, bonus_freshmen 추가
    db_models.py             # MODIFY: GameSaveRow에 pending_event, bonus_freshmen 컬럼 추가
  repositories/
    postgres.py              # MODIFY: pending_event, bonus_freshmen 직렬화/역직렬화
  api/
    routes/kakao.py          # MODIFY: event-choice 엔드포인트 추가
tests/
  test_events.py             # CREATE: 이벤트 로직 단위 테스트
```

## Module: events.py

### compute_education_power(save: SaveState) -> int

`GameEngine._education_power`와 동일한 계산을 독립 함수로 추출. `events.py`의 조건 필터링에서 사용. `game_engine.py`도 이 함수를 import하여 중복 제거.

```python
def compute_education_power(save: SaveState) -> int:
    from app.services.game_engine import DEPARTMENTS
    dept_boost = sum(DEPARTMENTS[d].education_boost for d in save.departments)
    return save.buildings.classroom * 8 + save.buildings.cafeteria * 2 + dept_boost
```

### pick_event(save: SaveState) -> EventDefinition | None

1. `random.random() >= 0.25` → return None
2. 조건 필터링:
   - `min_departments`: `len(save.departments) >= N`
   - `min_year`: `save.year >= N`
   - `min_buildings`: 총 건물 수 >= N
   - `min_labs`: `save.buildings.laboratory >= N`
   - `min_cafeteria`: `save.buildings.cafeteria >= N`
   - `min_education_power`: `compute_education_power(save) >= N`
   - `min_reputation`: 총 명성 >= N
   - `min_students`: `save.students.enrolled >= N`
3. 후보가 비어있으면 return None
4. 가중치 기반 `random.choices` → 1개 선택

### apply_event(save: SaveState, event: EventDefinition, choice: str | None) -> list[str]

- `choice=None`: effects 적용 (긍정/부정)
- `choice="a"`: effects 적용 (선택A)
- `choice="b"`: choice_b_effects 적용 (선택B)
- Effect Application Rules 테이블에 따라 save 변경
- 로그 메시지 리스트 반환

## advance_turn Integration

```python
# pending_event가 있으면 만료시키고 진행 (미응답 시 선택 기회 소멸)
if save.pending_event is not None:
    expired_event = EVENTS.get(save.pending_event)
    if expired_event:
        logs.append(f"⏰ '{expired_event.name}' 이벤트에 응답하지 않아 기회가 사라졌습니다.")
    save.pending_event = None

# 기존 코드: 예산 정산, 졸업/입학 처리 ...

# 이벤트 판정
event = pick_event(save)
if event is not None:
    if event.event_type in ("positive", "negative"):
        event_logs = apply_event(save, event, choice=None)
        logs.extend(event_logs)
    elif event.event_type == "choice":
        save.pending_event = event.id
        logs.append(f"📢 {event.name}: {event.description}")
```

선택형 이벤트 발생 시 quickReplies 변경:
```python
if save.pending_event is not None:
    quickReplies = ["선택 A", "선택 B", "내 대학 현황"]
```

### _apply_admission 변경

```python
freshmen = max(20, 110 - difficulty_penalty + round(dorm_capacity * 0.35) + save.bonus_freshmen)
# bonus_freshmen 적용 후 초기화
save.bonus_freshmen = 0
```

## New Endpoint: POST /webhooks/kakao/event-choice

```python
@router.post("/event-choice")
async def event_choice(request: KakaoWebhookRequest, repo: SaveRepository = Depends(get_repository)) -> dict:
    result = await game_engine.event_choice(request, repo)
    return to_kakao_response(result)
```

GameEngine.event_choice 로직:
1. `save.pending_event`가 None이면 → 에러 "진행 중인 이벤트가 없습니다."
2. `EVENTS[save.pending_event]`로 이벤트 정의 조회
3. 파라미터에서 choice ("a" 또는 "b") 추출
4. `apply_event(save, event, choice)` 호출
5. `save.pending_event = None`
6. 저장 후 결과 반환

## Kakao Open Builder 추가 설정

| 블록 이름 | 패턴 발화 | 스킬 | 파라미터 |
|-----------|----------|------|---------|
| 이벤트 선택A | "선택 A" | 이벤트 선택 | choice=a |
| 이벤트 선택B | "선택 B" | 이벤트 선택 | choice=b |

스킬 URL: `/webhooks/kakao/event-choice`

## Testing

### test_events.py

- `test_pick_event_returns_none_when_probability_fails`: seed 고정, 확률 미통과 시 None
- `test_pick_event_returns_none_when_no_conditions_met`: 초기 상태에서 조건 요구 이벤트 미발생
- `test_pick_event_returns_none_when_candidates_empty`: 필터 후 후보 0개
- `test_pick_event_respects_conditions`: 조건 충족 시 이벤트 후보에 포함
- `test_apply_positive_event_changes_budget`: budget +80 적용 확인
- `test_apply_negative_event_floors_at_zero`: budget 30에서 -60 적용 시 0
- `test_apply_event_reputation_leading`: 주력 분야에 명성 적용
- `test_apply_event_reputation_each`: 모든 분야에 균등 적용
- `test_apply_choice_event_a`: 선택A 효과 적용
- `test_apply_choice_event_b`: 선택B 효과 적용
- `test_compute_education_power`: 독립 함수 계산 결과 확인

### game_engine 테스트

- `test_advance_turn_can_trigger_event`: seed 고정으로 이벤트 발생 확인
- `test_choice_event_sets_pending`: 선택형 이벤트 시 pending_event 저장 확인
- `test_pending_event_expires_on_next_turn`: 미응답 시 다음 턴에서 만료 + 로그
- `test_event_choice_clears_pending`: 선택 후 pending_event가 None
- `test_bonus_freshmen_applied_in_march`: applicant_surge 이후 3월 입학 시 +15 반영 및 초기화

### API 통합 테스트

- `test_event_choice_endpoint_no_pending`: pending 없을 때 에러 응답
- `test_event_choice_endpoint_success`: 정상 선택 후 결과 확인
