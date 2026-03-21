# University Tycoon MVP Plan

## 1. Goal

첫 출시 목표는 `귀여운 모바일 경영 시뮬레이션`을 iPhone에서 플레이 가능하게 만들고, `TestFlight`를 거쳐 `App Store 심사 제출`까지 완료하는 것이다.

핵심 원칙:

- 빠르게 구현 가능한 구조
- 싱글플레이 중심
- 귀엽고 읽기 쉬운 UI
- 복잡한 시스템보다 플레이 루프 완성 우선

## 2. Recommended Stack

### Core

- `Expo`
- `React Native`
- `TypeScript`

### State / Storage

- 앱 전역 상태: `Zustand`
- 로컬 저장: `AsyncStorage`

### UI / Motion

- 기본 UI: React Native 컴포넌트
- 애니메이션: `react-native-reanimated`
- 아이콘/일러스트 에셋: Figma + AI 이미지 생성 결과물 사용

### Why this stack

- 웹 프론트 문법과 유사해서 진입 장벽이 낮음
- iOS 빌드와 테스트 흐름이 비교적 단순함
- 2D 시뮬레이션 UI 구현에 충분함
- 첫 버전에서는 서버 없이도 완성 가능함

## 3. MVP Product Definition

### Player Fantasy

플레이어는 작은 대학을 운영하면서 캠퍼스를 확장하고, 학생 모집과 졸업 성과를 통해 대학 명성을 키운다.

### Core Game Loop

1. 월이 진행된다.
2. 플레이어는 예산을 사용해 건물을 짓거나 학과를 개설한다.
3. 10월에 입학 기준을 설정한다.
4. 3월에 신입생이 들어오고 학과에 배치된다.
5. 2월에 졸업 결과가 발생하고 명성이 오른다.
6. 총 명성과 예산이 성장한다.

## 4. MVP Scope

### Include

- 월 단위 진행 시스템
- 예산 시스템
- 총 명성 + 분야 명성 4종
- 캠퍼스 그리드 맵
- 건물 건설
- 학과 개설
- 입학 기준 설정
- 입학생 계산
- 졸업 결과 계산
- 저장 / 불러오기
- 계절에 따른 배경 변경
- 귀여운 모바일 UI

### Exclude

- 멀티플레이
- 로그인
- 클라우드 저장
- 광고 / 인앱결제
- 학생 개별 캐릭터 육성
- 복잡한 랜덤 이벤트 시스템
- 세부 튜토리얼 시나리오 다수
- 안드로이드 동시 출시

## 5. MVP Feature Breakdown

### 5.1 Time System

- 시작 시점: `1년 1월`
- 1턴 = 1개월
- `다음 달로 진행` 버튼 제공
- 월별 필수 이벤트:
  - `2월`: 졸업
  - `3월`: 입학
  - `10월`: 입학 기준 설정

### 5.2 Reputation System

사용 명성:

- 예체능
- 공학
- 의학
- 기초학문

표시 값:

- 분야별 명성
- 대학 총 명성 = 4개 분야 명성 합

### 5.3 Departments

첫 버전은 학과 수를 줄인다.

- 미술학과
- 컴퓨터공학과
- 의학과
- 인문학과

각 학과 속성:

- 소속 분야
- 개설 비용
- 학생 수용량
- 기본 교육력 기여치

### 5.4 Buildings

첫 버전 건물:

- 강의실
- 기숙사
- 연구소
- 식당

건물 효과:

- 강의실: 학생 수용량, 교육력 증가
- 기숙사: 입학생 수 증가
- 연구소: 연구력 및 해당 분야 명성 증가
- 식당: 학생 유지율 보정

### 5.5 Admission

10월에 과목 기준 설정:

- 수학
- 과학
- 영어
- 국어

등급 범위:

- `1 ~ 9`

간단 계산식:

- 입학 난이도 = 4과목 평균 기준
- 학생 수준 = `10 - 평균 등급`
- 입학생 수 = `기본 학생 수 - 입학 난이도 보정 + 기숙사 보정`

### 5.6 Graduation

2월에 졸업 결과 계산:

영향 요소:

- 학생 수준
- 연구력
- 교육력

결과 타입:

- 교수
- 대기업 취업
- 창업 성공
- 일반 취업

결과에 따라 명성 증가.

### 5.7 Campus Map

- `5 x 5` 그리드로 시작
- 빈 칸 선택 시 건설 팝업 오픈
- 배치 완료 후 건물 아이콘 표시
- 건물별 색상과 아이콘을 다르게 사용

### 5.8 UX / Screens

필수 화면:

- 스플래시
- 메인 게임 화면
- 건설 팝업
- 학과 개설 팝업
- 입학 기준 설정 팝업
- 월 결과 팝업
- 설정 / 저장 화면

## 6. Cute Visual Direction

### Art Style

- 둥근 모서리
- 파스텔 계열 색상
- 과하지 않은 그림자
- 작은 애니메이션
- 귀여운 아이콘형 건물

### Tone

- 부담 없는 캐주얼 경영 게임
- 숫자는 명확하게, 비주얼은 부드럽게
- 화면이 복잡해 보이지 않도록 카드형 UI 사용

### Suggested Design Workflow

1. Figma에서 화면 구조 설계
2. Figma AI 또는 Figma Make로 빠른 시안 생성
3. ChatGPT 이미지 생성으로 건물 아이콘/마스코트 초안 제작
4. Canva 또는 Adobe Express로 색감/텍스트 정리
5. 최종 에셋을 PNG 또는 SVG로 정리

## 7. Technical Structure

### Suggested App Structure

```text
src/
  components/
  screens/
  features/
    campus/
    students/
    departments/
    progression/
  store/
  data/
  utils/
  assets/
```

### Suggested State Shape

```ts
type GameState = {
  year: number;
  month: number;
  budget: number;
  reputation: {
    arts: number;
    engineering: number;
    medical: number;
    humanities: number;
  };
  stats: {
    educationPower: number;
    researchPower: number;
    dormCapacity: number;
    studentCapacity: number;
  };
  students: {
    enrolled: number;
    averageLevel: number;
  };
  departments: DepartmentInstance[];
  buildings: BuildingInstance[];
  admissionCriteria: {
    math: number;
    science: number;
    english: number;
    korean: number;
  };
};
```

## 8. Success Criteria

MVP 완료 기준:

- iPhone에서 정상 플레이 가능
- 새 게임 시작 / 저장 / 불러오기 가능
- 12개월 이상 진행 가능
- 입학 / 졸업 이벤트가 정상 동작
- 건물 건설과 학과 개설이 게임 결과에 영향을 줌
- TestFlight 배포 성공
- App Store 심사 제출 가능 상태 도달
