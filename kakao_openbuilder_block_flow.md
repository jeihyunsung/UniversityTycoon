# University Tycoon Kakao Open Builder Block Flow

## 1. Purpose

이 문서는 `University Tycoon` 카카오톡 챗봇판의 오픈빌더 블록 구조와 대화 흐름을 구현 수준으로 정리한 문서다.

목표:

- 오픈빌더에서 어떤 블록을 만들어야 하는지 명확히 하기
- 어떤 블록이 스킬 서버를 호출하는지 구분하기
- 사용자가 어디서든 메인 루프로 복귀할 수 있게 하기

## 2. Design Principles

- 블록 수는 많아도 역할은 단순하게 유지
- 룰 블록은 안내와 라우팅 담당
- 스킬 블록은 상태 조회와 게임 계산 담당
- 모든 주요 화면에서 `메인 메뉴`로 돌아갈 수 있어야 함

## 3. Top-Level Conversation Structure

전체 흐름은 아래처럼 본다.

```text
시작
-> 온보딩 / 새 게임 여부 확인
-> 메인 메뉴
-> 액션 선택
-> 스킬 실행
-> 결과 표시
-> 메인 메뉴 복귀 또는 다음 달 진행
```

## 4. Required Blocks

### Rule Blocks

- `entry`
- `help`
- `fallback`
- `main_menu_router`
- `restart_confirm`

### Skill Blocks

- `start_game`
- `load_status`
- `advance_turn`
- `build_menu`
- `build_execute`
- `department_menu`
- `department_execute`
- `admission_menu`
- `admission_execute`
- `recent_logs`

## 5. Block Catalog

## 5.1 `entry`

### Type

- Rule block

### Purpose

- 최초 진입점
- 새 유저와 기존 유저를 분기

### User Entry Examples

- 안녕
- 시작
- 대학경영게임

### Action

- `start_game` 스킬 블록 또는 `load_status` 스킬 블록으로 연결

### Response Shape

- simpleText
- quickReplies

### Quick Replies

- 새 게임 시작
- 이어서 하기
- 도움말

## 5.2 `start_game`

### Type

- Skill block

### Purpose

- 사용자 신규 세이브 생성
- 초기 상태 저장

### Success Response

```text
작은 대학 운영이 시작되었습니다.
현재 1년 1월 / 예산 480G / 총 명성 30
무엇부터 해볼까요?
```

### Quick Replies

- 내 대학 현황
- 건물 건설
- 학과 개설
- 다음 달 진행

## 5.3 `load_status`

### Type

- Skill block

### Purpose

- 현재 저장 상태 조회
- 재진입 유저를 메인 루프로 복귀

### Response Content

- 연도 / 월
- 예산
- 총 명성
- 재학생
- 최근 이벤트 1줄

### Quick Replies

- 다음 달 진행
- 건물 건설
- 학과 개설
- 입학 정책
- 지난 결과 보기

## 5.4 `main_menu_router`

### Type

- Rule block

### Purpose

- 자연어 또는 버튼 입력을 각 기능 블록으로 분기

### Routes

- 내 대학 현황 -> `load_status`
- 다음 달 진행 -> `advance_turn`
- 건물 건설 -> `build_menu`
- 학과 개설 -> `department_menu`
- 입학 정책 -> `admission_menu`
- 지난 결과 보기 -> `recent_logs`
- 도움말 -> `help`

## 5.5 `advance_turn`

### Type

- Skill block

### Purpose

- 월 진행
- 월간 정산
- 2월 / 3월 / 10월 이벤트 자동 처리

### Response Pattern

1. 현재 달 결과 요약
2. 이벤트 발생 시 추가 요약
3. 다음 행동 제안

### Example Response

```text
1년 2월이 끝났습니다.
운영 결과: 등록금 220G / 유지비 68G / 순변화 +152G
졸업 성과로 총 명성 +18이 올랐습니다.

이제 1년 3월입니다.
무엇을 하시겠어요?
```

### Quick Replies

- 다음 달 진행
- 건물 건설
- 학과 개설
- 내 대학 현황

## 5.6 `build_menu`

### Type

- Skill block

### Purpose

- 현재 예산 기준 건설 가능한 시설 목록 출력

### Response Content

- 각 건물명
- 비용
- 핵심 효과
- 현재 보유 수량

### Quick Replies

- 강의실 건설
- 기숙사 건설
- 연구소 건설
- 식당 건설
- 메인 메뉴

## 5.7 `build_execute`

### Type

- Skill block

### Purpose

- 선택한 건물 1개 건설 처리

### Input

- building_type

### Success Response

```text
강의실을 건설했습니다.
예산 -120G
학생 수용량 +60 / 교육력 +8
```

### Fail Cases

- 예산 부족
- 잘못된 building_type
- 세이브 없음

### Quick Replies

- 계속 건설
- 내 대학 현황
- 다음 달 진행

## 5.8 `department_menu`

### Type

- Skill block

### Purpose

- 개설 가능한 학과와 조건 출력

### Response Content

- 학과명
- 비용
- 효과
- 개설 여부

### Quick Replies

- 미술학과
- 컴퓨터공학과
- 의학과
- 인문학과
- 메인 메뉴

## 5.9 `department_execute`

### Type

- Skill block

### Purpose

- 학과 개설 처리

### Input

- department_id

### Success Response

```text
컴퓨터공학과를 개설했습니다.
예산 -150G
공학 명성 +4 / 학생 수용량 +45
```

### Fail Cases

- 이미 개설됨
- 예산 부족
- 명성 조건 미충족

## 5.10 `admission_menu`

### Type

- Skill block

### Purpose

- 현재 입학 정책 상태와 변경 옵션 표시

### Recommendation

MVP는 프리셋 정책 3개만 제공:

- 쉬움
- 보통
- 엄격

### Response Example

```text
현재 입학 정책은 `보통`입니다.
정책이 엄격할수록 학생 수준은 올라가지만 입학생 수는 줄어듭니다.
```

### Quick Replies

- 쉬움
- 보통
- 엄격
- 메인 메뉴

## 5.11 `admission_execute`

### Type

- Skill block

### Purpose

- 입학 정책 프리셋 저장

### Input

- policy_level

### Success Response

```text
입학 정책을 `엄격`으로 변경했습니다.
앞으로 입학생 수는 줄 수 있지만 학생 평균 수준이 높아집니다.
```

## 5.12 `recent_logs`

### Type

- Skill block

### Purpose

- 최근 5턴 로그 출력

### Response Pattern

- 최신순 3~5개 요약
- 너무 길면 자르기

### Quick Replies

- 내 대학 현황
- 다음 달 진행
- 메인 메뉴

## 5.13 `help`

### Type

- Rule block

### Purpose

- 플레이 방법 안내

### Response Example

```text
이 게임은 월 단위 대학 운영 시뮬레이션입니다.
건물을 짓고, 학과를 열고, 입학 정책을 조정하면서 명성을 올리세요.
```

### Quick Replies

- 내 대학 현황
- 새 게임 시작
- 메인 메뉴

## 5.14 `restart_confirm`

### Type

- Rule block

### Purpose

- 새 게임 시작 전 확인

### Quick Replies

- 정말 초기화
- 취소

## 5.15 `fallback`

### Type

- Rule block

### Purpose

- 의도 해석 실패 시 메인 메뉴 복귀

### Response Example

```text
이 명령은 아직 이해하지 못했어요.
아래 메뉴 중 하나를 선택해주세요.
```

## 6. Main Flow

### First-Time User

```text
entry
-> start_game
-> load_status
-> build_menu or advance_turn
```

### Returning User

```text
entry
-> load_status
-> main_menu_router
-> selected skill block
-> result
-> load_status or main_menu_router
```

## 7. Button Mapping Strategy

빠른 답장은 내부적으로 아래 액션 코드와 연결하는 것을 권장한다.

- `ACTION_STATUS`
- `ACTION_ADVANCE`
- `ACTION_BUILD_MENU`
- `ACTION_BUILD_CLASSROOM`
- `ACTION_BUILD_DORMITORY`
- `ACTION_BUILD_LAB`
- `ACTION_BUILD_CAFETERIA`
- `ACTION_DEPT_ART`
- `ACTION_DEPT_COMPUTER`
- `ACTION_DEPT_MEDICAL`
- `ACTION_DEPT_HUMANITIES`
- `ACTION_ADMISSION_EASY`
- `ACTION_ADMISSION_NORMAL`
- `ACTION_ADMISSION_HARD`
- `ACTION_LOGS`
- `ACTION_HELP`

이렇게 하면 자연어 매칭보다 훨씬 안정적이다.

## 8. Recommended Kakao Response Components

MVP에서 가장 많이 쓸 조합:

- `simpleText`
- `basicCard`
- `quickReplies`

권장 패턴:

- 정보 조회: `simpleText + quickReplies`
- 선택 메뉴: `basicCard + quickReplies`
- 결과 리포트: `simpleText + quickReplies`

## 9. Error Handling Rules

- 세이브가 없으면 `새 게임 시작` 유도
- 예산 부족이면 바로 이유와 현재 예산 표시
- 중복 개설이면 이미 개설됐다고 안내
- 서버 오류 시 짧은 사과 문구 + 메인 메뉴 복귀

## 10. Practical Build Order

오픈빌더 구현 순서:

1. `entry`
2. `start_game`
3. `load_status`
4. `main_menu_router`
5. `advance_turn`
6. `build_menu`
7. `build_execute`
8. `department_menu`
9. `department_execute`
10. `admission_menu`
11. `admission_execute`
12. `recent_logs`
13. `help`
14. `fallback`

## 11. Final Rule

오픈빌더 안에서 게임 로직을 처리하려고 하지 말고, 상태 계산은 항상 스킬 서버에 맡긴다. 오픈빌더는 `사용자 의도 라우팅과 응답 배치`에 집중하는 것이 가장 안전하다.
