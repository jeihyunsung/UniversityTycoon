# Dynamic Titles System Design

## Goal

플레이어의 현재 스탯에 따라 자동으로 갱신되는 동적 칭호를 부여한다. 퀘스트 칭호(title)와 별도로 표시된다.

## Architecture

`titles.py` 독립 모듈에 `compute_dynamic_title(save) -> str` 함수 1개. 저장 불필요 — 매 조회 시 계산. `load_status`와 `quests` 메서드에서 호출하여 표시.

## Title Rules

우선순위 순서로 체크. 첫 번째 매칭을 반환:

| 우선순위 | 칭호 | 조건 |
|---------|------|------|
| 1 | 연구 특화 대학 | research_power >= 30 AND laboratory >= 3 |
| 2 | 교육 특화 대학 | education_power >= 40 AND classroom >= 3 |
| 3 | 예체능 명문 | arts가 최고 분야 AND arts >= 30 |
| 3 | 공학 명문 | engineering이 최고 AND engineering >= 30 |
| 3 | 의학 명문 | medical이 최고 AND medical >= 30 |
| 3 | 인문 명문 | humanities이 최고 AND humanities >= 30 |
| 4 | 사업형 대학 | budget >= 1000 |
| 5 | 대규모 대학 | enrolled >= 200 |
| 6 | 성장하는 대학 | total_reputation >= 40 |
| 7 | 작은 대학 | 기본값 |

우선순위 3은 leading_field로 결정. 동점 시 기존 leading_field 규칙 적용 (arts > engineering > medical > humanities 순).

## Display Format

현황 조회 (`load_status`):
```
1년 3월입니다. 예산 480G / 총 명성 30 / 재학생 72명
🏷 연구 특화 대학 | 🎓 종합 대학
📋 다음 목표: 캠퍼스 확장 (건물 2/3개)
```

퀘스트 화면 (`quests`):
```
🎓 종합 대학 | 🏷 연구 특화 대학
【마일스톤】
...
```

## Dependencies

- `events.py`: `compute_education_power`, `total_reputation`, `leading_field` import
- `game_engine.py`: `_research_power` 계산 (또는 독립 함수로 추출)

`_research_power`는 현재 GameEngine의 private 메서드. `events.py`에 `compute_research_power(save)` 독립 함수로 추출하여 공유.

## File Structure

```
chatbot-server/app/services/
  titles.py              # CREATE: compute_dynamic_title()
  events.py              # MODIFY: add compute_research_power()
  game_engine.py         # MODIFY: load_status/quests에 동적 칭호 표시, _research_power 위임
tests/
  test_titles.py         # CREATE
```

## Testing

- `test_default_title`: 초기 상태 → "작은 대학"
- `test_growing_title`: 총 명성 40+ → "성장하는 대학"
- `test_research_title`: 연구력 30+ AND 연구소 3+ → "연구 특화 대학"
- `test_education_title`: 교육력 40+ AND 강의실 3+ → "교육 특화 대학"
- `test_field_title`: arts 최고 30+ → "예체능 명문"
- `test_business_title`: budget 1000+ → "사업형 대학"
- `test_large_title`: enrolled 200+ → "대규모 대학"
- `test_priority_order`: 여러 조건 동시 충족 시 우선순위 높은 것 반환
