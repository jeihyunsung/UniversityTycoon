# University Tycoon Kakao Skill Server API Spec

## 1. Purpose

이 문서는 카카오 오픈빌더와 연동할 `FastAPI` 기반 스킬 서버의 API 스펙 초안이다.

목표:

- 어떤 엔드포인트가 필요한지 정의
- 요청/응답 구조를 통일
- 게임 상태와 대화 상태 저장 규칙을 명확히 하기

## 2. Architecture Summary

권장 구조:

- `FastAPI`
- `PostgreSQL`
- ORM: `SQLAlchemy` 또는 `SQLModel`
- 배포: Render, Railway, Fly.io, AWS 중 하나

외부 흐름:

```text
Kakao Open Builder
-> Skill Webhook
-> FastAPI
-> Game Service
-> PostgreSQL
-> Kakao Response JSON
```

## 3. API Design Rule

- 각 API는 하나의 게임 액션만 처리
- 응답은 `internal payload`와 `kakao response body`를 분리 가능하게 설계
- 서버 내부에서는 도메인 모델 반환
- 최종 라우터에서 카카오 응답 형식으로 변환

## 4. Core Domain Objects

## 4.1 PlayerSave

```json
{
  "userId": "usr_123",
  "year": 1,
  "month": 3,
  "budget": 520,
  "reputation": {
    "arts": 8,
    "engineering": 14,
    "medical": 6,
    "humanities": 12
  },
  "students": {
    "enrolled": 84,
    "averageLevel": 5.4
  },
  "admissionPolicy": "normal",
  "buildings": {
    "classroom": 2,
    "dormitory": 1,
    "laboratory": 1,
    "cafeteria": 0
  },
  "departments": [
    "humanities",
    "computer"
  ]
}
```

## 4.2 ConversationState

```json
{
  "userId": "usr_123",
  "currentBlock": "BUILD_MENU",
  "lastAction": "ACTION_BUILD_MENU",
  "updatedAt": "2026-03-15T23:20:00+09:00"
}
```

## 5. Authentication / User Identification

카카오 요청 본문에서 사용자 식별값을 추출해 내부 `user_id`로 매핑해야 한다.

권장:

- `kakao_user_key` 저장
- 없으면 챗봇 요청의 유저 식별 필드를 내부 해시 키로 변환

주의:

- 사용자 식별 필드 이름은 실제 오픈빌더 요청 포맷에 맞춰 구현 시점에 최종 확인 필요
- 이 문서에서는 `kakao_user_key`라는 내부 개념으로 통일

## 6. Endpoint List

MVP 권장 엔드포인트:

- `POST /webhooks/kakao/start-game`
- `POST /webhooks/kakao/status`
- `POST /webhooks/kakao/advance-turn`
- `POST /webhooks/kakao/build-menu`
- `POST /webhooks/kakao/build`
- `POST /webhooks/kakao/department-menu`
- `POST /webhooks/kakao/department`
- `POST /webhooks/kakao/admission-menu`
- `POST /webhooks/kakao/admission`
- `POST /webhooks/kakao/logs`

## 7. Shared Request Model

모든 엔드포인트에서 최소한 아래 정보는 필요하다.

```json
{
  "user": {
    "kakaoUserKey": "kakao_abc123"
  },
  "action": {
    "name": "ACTION_BUILD_CLASSROOM",
    "params": {}
  },
  "context": {
    "channelId": "channel_xxx",
    "blockId": "build_execute"
  },
  "rawKakaoPayload": {}
}
```

실제로는 오픈빌더 원본 요청을 그대로 받아 내부 DTO로 파싱하는 구조가 좋다.

## 8. Shared Response Model

서버 내부 응답 표준:

```json
{
  "ok": true,
  "message": "강의실을 건설했습니다.",
  "save": {},
  "logs": [],
  "quickReplies": [],
  "errorCode": null
}
```

최종적으로는 이를 카카오 응답 포맷으로 변환한다.

## 9. Endpoint Details

## 9.1 `POST /webhooks/kakao/start-game`

### Purpose

- 새 게임 시작
- 기존 저장이 있으면 초기화 옵션 처리 가능

### Request

```json
{
  "user": {
    "kakaoUserKey": "kakao_abc123"
  }
}
```

### Logic

- 유저가 없으면 생성
- 세이브 생성 또는 덮어쓰기
- 초기 로그 생성

### Response

```json
{
  "ok": true,
  "message": "작은 대학 운영이 시작되었습니다.",
  "save": {
    "year": 1,
    "month": 1,
    "budget": 480
  },
  "quickReplies": [
    "내 대학 현황",
    "건물 건설",
    "학과 개설",
    "다음 달 진행"
  ]
}
```

## 9.2 `POST /webhooks/kakao/status`

### Purpose

- 현재 상태 조회

### Logic

- 유저 세이브 조회
- 최근 로그 1개 포함
- 메인 메뉴 응답 생성

### Response Example

```json
{
  "ok": true,
  "message": "1년 4월입니다. 예산 430G / 총 명성 42 / 재학생 80명",
  "save": {
    "year": 1,
    "month": 4
  },
  "quickReplies": [
    "다음 달 진행",
    "건물 건설",
    "학과 개설",
    "입학 정책",
    "지난 결과 보기"
  ]
}
```

## 9.3 `POST /webhooks/kakao/advance-turn`

### Purpose

- 월 진행
- 예산 정산
- 예약 이벤트 처리

### Logic

- 현재 저장 상태 로드
- 다음 월 계산
- 운영 수입/지출 반영
- 2월이면 졸업 처리
- 3월이면 입학 처리
- 10월이면 정책 변경 유도 문구 추가
- 저장 후 결과 반환

### Response Example

```json
{
  "ok": true,
  "message": "1년 2월이 끝났습니다. 운영 결과 +152G. 졸업 성과로 총 명성 +18",
  "logs": [
    "졸업생 14명 배출",
    "교수 1명, 대기업 4명, 창업 1명"
  ],
  "quickReplies": [
    "다음 달 진행",
    "건물 건설",
    "내 대학 현황"
  ]
}
```

## 9.4 `POST /webhooks/kakao/build-menu`

### Purpose

- 건설 가능 목록 조회

### Logic

- 현재 예산 로드
- 건물 정의 테이블 조합
- 건설 가능/불가 표시

### Response Example

```json
{
  "ok": true,
  "message": "건설 가능한 시설 목록입니다.",
  "options": [
    {
      "id": "classroom",
      "label": "강의실",
      "cost": 120,
      "available": true
    },
    {
      "id": "laboratory",
      "label": "연구소",
      "cost": 180,
      "available": false
    }
  ],
  "quickReplies": [
    "강의실 건설",
    "기숙사 건설",
    "연구소 건설",
    "식당 건설"
  ]
}
```

## 9.5 `POST /webhooks/kakao/build`

### Purpose

- 선택 건물 건설 처리

### Request

```json
{
  "user": {
    "kakaoUserKey": "kakao_abc123"
  },
  "action": {
    "name": "ACTION_BUILD_CLASSROOM",
    "params": {
      "buildingType": "classroom"
    }
  }
}
```

### Logic

- 세이브 조회
- 예산 확인
- 건물 수량 증가
- 예산 차감
- 스탯 재계산
- 로그 저장

### Success Response

```json
{
  "ok": true,
  "message": "강의실을 건설했습니다. 예산 -120G / 학생 수용량 +60 / 교육력 +8",
  "quickReplies": [
    "계속 건설",
    "내 대학 현황",
    "다음 달 진행"
  ]
}
```

### Error Response

```json
{
  "ok": false,
  "message": "예산이 부족합니다. 현재 예산은 90G입니다.",
  "errorCode": "NOT_ENOUGH_BUDGET",
  "quickReplies": [
    "내 대학 현황",
    "다음 달 진행"
  ]
}
```

## 9.6 `POST /webhooks/kakao/department-menu`

### Purpose

- 개설 가능한 학과 목록 조회

### Response Content

- 학과명
- 비용
- 개설 여부
- 필요한 조건

## 9.7 `POST /webhooks/kakao/department`

### Purpose

- 학과 개설 처리

### Request

```json
{
  "user": {
    "kakaoUserKey": "kakao_abc123"
  },
  "action": {
    "name": "ACTION_DEPT_COMPUTER",
    "params": {
      "departmentId": "computer"
    }
  }
}
```

### Success Response

```json
{
  "ok": true,
  "message": "컴퓨터공학과를 개설했습니다. 예산 -150G / 공학 명성 +4 / 학생 수용량 +45",
  "quickReplies": [
    "다른 학과 보기",
    "내 대학 현황",
    "다음 달 진행"
  ]
}
```

## 9.8 `POST /webhooks/kakao/admission-menu`

### Purpose

- 현재 입학 정책과 변경 옵션 조회

### Response Example

```json
{
  "ok": true,
  "message": "현재 입학 정책은 보통입니다. 정책을 엄격하게 할수록 학생 수준은 오르지만 수는 줄어듭니다.",
  "quickReplies": [
    "쉬움",
    "보통",
    "엄격",
    "메인 메뉴"
  ]
}
```

## 9.9 `POST /webhooks/kakao/admission`

### Purpose

- 입학 정책 변경

### Request

```json
{
  "user": {
    "kakaoUserKey": "kakao_abc123"
  },
  "action": {
    "name": "ACTION_ADMISSION_HARD",
    "params": {
      "policyLevel": "hard"
    }
  }
}
```

### Success Response

```json
{
  "ok": true,
  "message": "입학 정책을 엄격으로 변경했습니다. 앞으로 학생 수는 줄 수 있지만 평균 수준이 높아집니다.",
  "quickReplies": [
    "내 대학 현황",
    "다음 달 진행",
    "메인 메뉴"
  ]
}
```

## 9.10 `POST /webhooks/kakao/logs`

### Purpose

- 최근 5턴 로그 조회

### Response Example

```json
{
  "ok": true,
  "message": "최근 운영 기록입니다.",
  "logs": [
    "1년 4월: 강의실 건설",
    "1년 3월: 신입생 28명 입학",
    "1년 2월: 졸업 성과로 명성 +18"
  ],
  "quickReplies": [
    "내 대학 현황",
    "다음 달 진행",
    "메인 메뉴"
  ]
}
```

## 10. Kakao Response Adapter

FastAPI 라우터 마지막 단계에서 내부 응답을 카카오 응답 JSON으로 변환한다.

권장 변환 규칙:

- `message` -> simpleText
- `options` 또는 시각적 선택 정보 -> basicCard description/items
- `quickReplies` -> quickReplies 배열

예시 구조:

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "1년 4월입니다. 예산 430G / 총 명성 42 / 재학생 80명"
        }
      }
    ],
    "quickReplies": [
      {
        "label": "다음 달 진행",
        "action": "message",
        "messageText": "다음 달 진행"
      }
    ]
  }
}
```

응답 필드 명세의 세부값은 실제 오픈빌더 스킬 테스트에서 최종 맞춰야 한다.

## 11. Service Layer Modules

FastAPI 내부 추천 모듈:

```text
app/
  main.py
  api/
    kakao_webhooks.py
  services/
    game_service.py
    turn_service.py
    build_service.py
    department_service.py
    admission_service.py
    response_adapter.py
  repositories/
    user_repository.py
    save_repository.py
    log_repository.py
  models/
    db_models.py
    schemas.py
```

## 12. Validation Rules

- 존재하지 않는 유저는 상태 조회 시 새 게임 유도
- 존재하지 않는 액션 코드는 fallback 응답
- 이미 개설된 학과는 중복 처리 금지
- 예산이 음수가 되면 안 됨
- 월 진행은 항상 `1 -> 12 -> 1` 순환
- 2월 졸업, 3월 입학, 10월 정책 점검 이벤트는 자동 실행

## 13. Error Codes

권장 에러 코드:

- `SAVE_NOT_FOUND`
- `INVALID_ACTION`
- `NOT_ENOUGH_BUDGET`
- `ALREADY_OPENED`
- `INVALID_POLICY`
- `INTERNAL_ERROR`

## 14. Logging

최소 로그:

- request_id
- kakao_user_key
- endpoint
- action_name
- response_status
- latency_ms

운영 중에는 액션 성공률과 이탈 지점을 보는 것이 중요하다.

## 15. Test Priority

우선 테스트할 것:

1. 새 게임 시작
2. 상태 조회
3. 월 진행
4. 건설 성공 / 실패
5. 학과 개설 성공 / 실패
6. 입학 정책 변경
7. 2월 졸업 이벤트
8. 3월 입학 이벤트

## 16. Final Recommendation

실제 구현은 `오픈빌더는 얇게`, `FastAPI는 두껍게` 가져가는 것이 가장 좋다.

- 오픈빌더: 메뉴와 라우팅
- FastAPI: 게임 규칙과 저장
- PostgreSQL: 세이브와 로그

이 구조가 디버깅과 확장 모두 가장 쉽다.
