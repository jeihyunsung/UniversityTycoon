# Kakao Open Builder 연동 가이드

## 사전 준비
1. Kakao Developers 계정 생성: https://developers.kakao.com
2. 카카오톡 채널 생성 (카카오 비즈니스 > 카카오톡 채널)
3. 오픈빌더에서 봇 생성: https://chatbot.kakao.com

## 스킬 서버 등록
1. 오픈빌더 > 스킬 > 스킬 생성
2. URL: `https://<your-render-url>/webhooks/kakao`
3. 각 스킬별 엔드포인트 등록:

| 스킬 이름 | URL 경로 |
|-----------|----------|
| 게임 시작 | /webhooks/kakao/start-game |
| 대학 현황 | /webhooks/kakao/status |
| 다음 달 진행 | /webhooks/kakao/advance-turn |
| 건설 메뉴 | /webhooks/kakao/build-menu |
| 건물 건설 | /webhooks/kakao/build |
| 학과 메뉴 | /webhooks/kakao/department-menu |
| 학과 개설 | /webhooks/kakao/department |
| 입학 정책 메뉴 | /webhooks/kakao/admission-menu |
| 입학 정책 변경 | /webhooks/kakao/admission |
| 운영 기록 | /webhooks/kakao/logs |

## 시나리오 블록 설정

### 웰컴 블록
- 트리거: 사용자 최초 진입
- 스킬: 게임 시작
- 빠른 답장: 내 대학 현황, 건물 건설, 학과 개설, 다음 달 진행

### 메인 메뉴 블록
- 트리거: "내 대학 현황", "메인 메뉴"
- 스킬: 대학 현황

### 턴 진행 블록
- 트리거: "다음 달 진행"
- 스킬: 다음 달 진행

### 건설 블록
- 트리거: "건물 건설", "계속 건설"
- 스킬: 건설 메뉴

### 건물 선택 블록 (4개)
- 트리거: "강의실 건설", "기숙사 건설", "연구소 건설", "식당 건설"
- 스킬: 건물 건설
- 파라미터: buildingType = classroom / dormitory / laboratory / cafeteria

### 학과 블록
- 트리거: "학과 개설", "다른 학과 보기"
- 스킬: 학과 메뉴

### 학과 선택 블록 (4개)
- 트리거: "미술학과", "컴퓨터공학과", "의학과", "인문학과"
- 스킬: 학과 개설
- 파라미터: departmentId = art / computer / medical / humanities

### 입학 정책 블록
- 트리거: "입학 정책"
- 스킬: 입학 정책 메뉴

### 정책 선택 블록 (3개)
- 트리거: "쉬움", "보통", "엄격"
- 스킬: 입학 정책 변경
- 파라미터: policyLevel = easy / normal / hard

### 기록 블록
- 트리거: "지난 결과 보기"
- 스킬: 운영 기록

## 테스트
1. 오픈빌더 > 봇 테스트에서 시나리오 동작 확인
2. 카카오톡 채널에 봇 배포
3. 카카오톡에서 채널 친구 추가 후 대화 시작
