# University Tycoon for Kakao Chatbot

## 1. Purpose

이 문서는 현재 `University Tycoon` 앱형 설계를 `카카오톡 챗봇`으로 옮길 때 필요한 제품 구조, 대화 설계, 서버 구조, 저장 모델, MVP 범위를 정리한 문서다.

핵심 목표:

- 카카오톡 채팅방 안에서 플레이 가능한 대학 경영 게임 만들기
- 앱 UI 중심 구조를 대화형 UX로 재구성하기
- 카카오 오픈빌더와 스킬 서버 구조에 맞는 현실적인 MVP를 정의하기

## 2. Platform Assumptions

이 문서는 아래 전제를 기준으로 작성한다.

- 카카오톡 채널 기반 챗봇 사용
- 오픈빌더 시나리오 + 스킬 서버 연동 구조 사용
- 게임 데이터는 외부 서버 DB에 저장
- 사용자는 카카오톡 채팅방에서 버튼과 빠른 답장 중심으로 플레이

공식 문서상 카카오 챗봇은 카카오톡 채널과 함께 활용되며, 카카오싱크를 붙이면 가입 동선과 사용자 식별을 강화할 수 있다. 또 오픈 API/웹훅 테스트 및 카카오톡 채널 연결 관련 기능은 Kakao Developers에서 계속 제공 중이다.

출처:

- https://developers.kakao.com/product/kakaoTalkChannel
- https://developers.kakao.com/product/kakaoSync
- https://developers.kakao.com/docs/latest/ko/kakaosync/plugin
- https://developers.kakao.com/docs/latest/en/tool/webhook-test

## 3. Big Difference From App Version

앱 버전과 챗봇 버전의 차이는 매우 크다.

### App Version Strength

- 캠퍼스 맵을 한눈에 보여주기 쉬움
- 수치와 상태를 동시에 많이 보여줄 수 있음
- 건물 배치 같은 공간형 인터랙션이 자연스러움

### Chatbot Version Strength

- 진입 장벽이 낮음
- 설치 없이 바로 플레이 가능
- 친구 공유와 재방문 유도가 쉬움
- 메뉴형 진행과 짧은 턴 플레이에 적합함

### Chatbot Version Weakness

- 그리드 맵 표현이 제한적임
- 한 화면에 많은 수치를 동시에 보여주기 어려움
- 자유 입력을 많이 받으면 UX가 급격히 나빠짐

결론:

- 챗봇판은 `대화형 경영 시뮬레이션`으로 재해석해야 한다.
- 앱판의 `캠퍼스 시각화`는 줄이고, `월 진행`, `선택`, `결과`, `성장` 루프를 강화해야 한다.

## 4. Recommended Product Direction

### Best Fit

카카오 챗봇판은 아래 방향이 가장 적합하다.

- 텍스트 기반 운영 시뮬레이션
- 버튼형 선택지 중심
- 월 단위 턴 진행
- 매월 1~3개의 선택만 제시
- 결과를 짧은 리포트로 요약

### Not Recommended

아래 요소는 챗봇 MVP에서 빼는 것이 좋다.

- 자유로운 그리드 건물 배치
- 복잡한 수치 입력
- 긴 설명문과 많은 메뉴 단계
- 학생 개별 캐릭터 관리

## 5. Chatbot MVP Core Loop

챗봇판 핵심 루프:

1. 현재 월 상태 요약을 보여준다.
2. 플레이어는 이번 달 행동 1개를 선택한다.
3. 시스템이 결과를 계산한다.
4. 예산, 명성, 학생 수를 갱신한다.
5. 다음 달로 진행할지 묻는다.

### Monthly Flow Example

```text
1년 10월입니다.
예산 520G / 총 명성 38 / 재학생 74명

이번 달에 무엇을 하시겠어요?
1. 강의실 건설
2. 기숙사 확장
3. 컴퓨터공학과 개설 준비
4. 입학 기준 조정
```

이 구조가 챗봇 UX에 가장 잘 맞는다.

## 6. UX Design Principles for Kakao Chatbot

### 6.1 One Turn, One Decision

- 한 턴에 결정은 1개만 크게 묻는다.
- 선택지가 4개를 넘지 않게 한다.

### 6.2 No Free-Form Input by Default

- 대부분의 입력은 버튼과 빠른 답장 사용
- 숫자 직접 입력은 가능하면 피한다

### 6.3 Short State Summary

- 상태 요약은 항상 같은 순서 유지
- 권장 순서:
  - 연도/월
  - 예산
  - 총 명성
  - 재학생 수
  - 이번 달 이벤트

### 6.4 Strong Re-entry Design

- 사용자가 중간에 나갔다 다시 들어와도 이어서 플레이할 수 있어야 함
- 항상 `내 대학 현황`, `다음 달 진행`, `건설`, `학과`, `도움말` 빠른 답장 제공

## 7. MVP Feature Translation

앱 설계의 각 기능을 챗봇형으로 바꾸면 아래와 같다.

### 7.1 Campus Map

앱판:

- 5x5 그리드 직접 배치

챗봇판:

- 맵 직접 배치 제거
- 건물 수량 기반 관리로 단순화

예:

- 강의실 2개
- 기숙사 1개
- 연구소 1개
- 식당 1개

필요하면 나중에 `간단한 맵 요약 이미지`를 카드 이미지로 보여줄 수 있다. 하지만 MVP에서는 수량형 관리가 더 적합하다.

### 7.2 Building System

챗봇판에서는 아래처럼 메뉴형으로 제공:

- 건설 가능한 건물 목록 표시
- 비용과 효과 표시
- 하나 선택 시 즉시 반영

예:

```text
건설 가능한 시설
- 강의실 120G: 학생 수용 +60, 교육력 +8
- 기숙사 140G: 기숙사 수용 +40
- 연구소 180G: 연구력 +10
```

### 7.3 Department System

- 학과 개설 메뉴 제공
- 이미 개설된 학과는 비활성 또는 안내 문구 처리
- 명성 조건이 있다면 조건 미충족 시 이유 설명

### 7.4 Admission System

입학 기준은 자유 입력보다 `난이도 프리셋` 방식이 낫다.

권장:

- 쉬움
- 보통
- 엄격

또는 과목별 직접 조정이 필요하면 버튼형 단계 선택:

- 수학 기준 올리기
- 과학 기준 올리기
- 완료

하지만 MVP에서는 `프리셋 방식`이 더 적합하다.

### 7.5 Graduation System

- 2월에 자동 실행
- 결과를 짧은 성과 리포트 형태로 출력

예:

```text
졸업 시즌 결과
교수 1명 / 대기업 취업 4명 / 창업 성공 1명 / 일반 취업 8명
총 명성 +28
```

## 8. Recommended Conversation Structure

### Top-Level Menu

항상 돌아갈 수 있는 메인 메뉴:

- 내 대학 현황
- 다음 달 진행
- 건물 건설
- 학과 개설
- 입학 정책
- 지난 결과 보기
- 도움말

### Suggested Scenario Blocks

- `start`
- `main_status`
- `next_turn`
- `build_menu`
- `build_confirm`
- `department_menu`
- `admission_policy`
- `monthly_result`
- `help`

## 9. Open Builder Design

오픈빌더에서는 룰 기반 블록과 스킬 블록을 섞는 구조가 적합하다.

### Rule-Based Blocks

적합한 역할:

- 시작 인사
- 도움말
- 단순 메뉴 이동
- 고정 안내 문구

### Skill Blocks

적합한 역할:

- 현재 게임 상태 조회
- 월 진행 계산
- 건설 처리
- 학과 개설 처리
- 입학/졸업 결과 계산
- 저장된 세이브 불러오기

즉, 게임 핵심 로직은 대부분 스킬 서버에서 처리해야 한다.

## 10. Server Architecture

### Recommended Backend

- `FastAPI` 또는 `Node.js + Express/NestJS`
- DB: `PostgreSQL`
- 캐시 또는 임시 세션: 필요 시 Redis

현재 프로젝트 흐름을 고려하면 아래 구성이 빠르다.

- 챗봇 스킬 서버: `FastAPI`
- 게임 로직: Python service layer
- 저장: PostgreSQL

### Why

- 턴 기반 계산 로직을 Python으로 옮기기 쉬움
- 테스트 코드 작성이 편함
- 배포 구성이 단순함

## 11. Data Model

최소한 아래 테이블이 필요하다.

### users

- id
- kakao_user_key
- created_at
- last_played_at

### game_saves

- id
- user_id
- year
- month
- budget
- reputation_arts
- reputation_engineering
- reputation_medical
- reputation_humanities
- enrolled_students
- average_student_level
- admission_policy
- current_phase
- updated_at

### buildings

- id
- save_id
- building_type
- quantity

### departments

- id
- save_id
- department_id
- opened

### turn_logs

- id
- save_id
- year
- month
- summary
- created_at

## 12. State Model

챗봇에서는 `대화 상태`와 `게임 상태`를 분리하는 것이 중요하다.

### Game State

- 실제 게임 진행 데이터

### Conversation State

- 사용자가 지금 어떤 선택 단계에 있는지

예:

- `MAIN_MENU`
- `BUILD_SELECT`
- `DEPARTMENT_SELECT`
- `ADMISSION_SELECT`
- `TURN_RESULT`

이 분리가 없으면 사용자가 이전 버튼을 누르거나 중간 발화를 했을 때 상태가 꼬이기 쉽다.

## 13. Request / Response Flow

권장 흐름:

1. 사용자가 버튼 또는 발화 전송
2. 오픈빌더가 스킬 서버 호출
3. 스킬 서버가 사용자 식별값과 현재 상태 조회
4. 게임 로직 실행
5. 새 게임 상태 저장
6. 카카오 응답 포맷으로 메시지 반환

응답은 카카오 챗봇 응답 JSON 구조에 맞춰 `simpleText`, `basicCard`, `quickReplies` 중심으로 구성하는 것이 현실적이다. 이는 카카오 스킬 응답 템플릿들이 일반적으로 사용하는 패턴이기도 하다. 이 문서에서는 공식 포맷 세부 명세 대신 실무 설계 방향만 다룬다.

참고:

- 공식 웹훅 테스트 도구가 제공됨: https://developers.kakao.com/docs/latest/en/tool/webhook-test

## 14. Recommended Response Pattern

가장 안정적인 응답 패턴:

- 본문 요약 1개
- 선택 카드 또는 텍스트 리스트 1개
- 빠른 답장 3~5개

예:

```text
1년 4월입니다.
예산 430G / 총 명성 42 / 재학생 80명
이번 달엔 무엇을 하시겠어요?
```

빠른 답장:

- 건물 건설
- 학과 개설
- 다음 달 진행
- 내 대학 현황

## 15. Balance Design for Chatbot

챗봇은 화면 체류 시간이 짧기 때문에 수치가 너무 미세하면 재미가 약해진다.

권장:

- 한 번의 선택이 체감되게 만들기
- 예산과 명성 변화량을 크게 보여주기
- 결과 문구를 감정적으로 표현하기

예:

- `학생 만족도가 올랐습니다`
- `지원자가 늘어날 것 같습니다`
- `졸업 성과가 좋아 평판이 크게 상승했습니다`

## 16. MVP Scope Recommendation

챗봇 MVP에 넣을 것:

- 새 게임 시작
- 내 대학 현황 조회
- 다음 달 진행
- 건물 4종 건설
- 학과 4종 개설
- 입학 정책 3단계 설정
- 2월 졸업 이벤트
- 3월 입학 이벤트
- 최근 5턴 로그 보기

챗봇 MVP에서 뺄 것:

- 맵 직접 배치
- 계절 배경 비주얼
- 세부 학생 분포 시뮬레이션
- 장식 시설 다수
- 자유도 높은 복합 메뉴

## 17. Monetization / Retention Ideas

출시 후 검토 가능한 요소:

- 주간 랭킹
- 친구 초대 시 시작 자금 보너스
- 매일 접속 보상
- 카카오톡 채널 메시지로 복귀 유도

단, MVP에서는 넣지 않는 것이 좋다.

## 18. Risks

### Risk 1. Too Much Complexity

앱형 설계를 그대로 가져오면 챗봇 UX가 무너진다.

대응:

- 맵 제거
- 선택지 축소
- 프리셋 중심 설계

### Risk 2. State Desync

대화 상태와 게임 상태가 엇갈릴 수 있다.

대응:

- 모든 액션을 서버 저장 기준으로 처리
- 대화 단계 상태를 명시적으로 저장
- 항상 `메인 메뉴로 돌아가기` 제공

### Risk 3. Weak Visual Appeal

챗봇은 앱보다 시각 정보가 약하다.

대응:

- 결과 메시지 문구를 더 매력적으로 작성
- 주요 카드 이미지와 아이콘 보강
- 필요 시 외부 웹뷰 페이지로 확장

## 19. Best Practical Strategy

가장 현실적인 전략은 아래 2단계다.

### Stage 1

- 카카오 챗봇판은 `텍스트 기반 경영 시뮬레이션 MVP`로 제작
- 핵심은 월 진행과 선택 결과 루프

### Stage 2

- 캠퍼스 요약 이미지를 붙이거나
- 외부 미니 웹뷰를 연동해 캠퍼스 시각화를 보강

즉, 처음부터 앱과 같은 UI를 챗봇 안에서 구현하려고 하면 안 된다.

## 20. Final Recommendation

현재 설계를 카카오 챗봇으로 옮길 때 가장 좋은 구조는 이것이다.

- `그리드 맵 게임`이 아니라 `대화형 대학 운영 게임`으로 재정의
- 오픈빌더는 메뉴/시나리오 담당
- 스킬 서버는 게임 로직/세이브 담당
- 게임 상태와 대화 상태를 분리 저장
- MVP는 `월 진행`, `건설`, `학과`, `입학`, `졸업`만 구현

이 방향이면 카카오톡 안에서 플레이 가능한 형태로 충분히 성립한다.
