# University Tycoon 6-Week Roadmap

## Overall Objective

6주 안에 `귀여운 iOS 시뮬레이션 게임 MVP`를 완성하고, `TestFlight 배포`와 `App Store 제출 준비`까지 끝낸다.

## Week 1 - Scope and Prototype

목표:

- MVP 기능 고정
- 프로젝트 초기 세팅
- 화면 구조 프로토타입 완성

작업:

- Expo + TypeScript 프로젝트 생성
- 폴더 구조 정리
- Zustand, AsyncStorage, Reanimated 세팅
- 게임 상태 모델 정의
- Figma에서 메인 화면 와이어프레임 제작
- 색상, 폰트, 카드 스타일 가이드 확정
- 캠퍼스 `5 x 5` 그리드 프로토타입 구현

완료 기준:

- 앱이 실행되고 메인 화면 레이아웃 확인 가능
- Figma에 핵심 화면 4종 초안 존재

## Week 2 - Core Simulation

목표:

- 월 진행과 기본 수치 시스템 구현

작업:

- 연도 / 월 진행 로직 구현
- 예산 시스템 구현
- 명성 시스템 구현
- 교육력 / 연구력 / 수용량 계산 함수 구현
- 월 결과 로그 UI 추가
- 더미 데이터 기반 상태 변화 확인

완료 기준:

- 버튼으로 월 진행 가능
- 진행에 따라 예산과 명성이 바뀜

## Week 3 - Campus and Building System

목표:

- 캠퍼스 건설 플레이 루프 구현

작업:

- 빈 타일 선택 인터랙션 구현
- 건설 팝업 구현
- 건물 데이터 테이블 작성
- 강의실 / 기숙사 / 연구소 / 식당 효과 연결
- 건물 배치 시 상태 재계산 로직 연결
- 건물 아이콘 1차 적용

완료 기준:

- 플레이어가 건물을 짓고 효과를 즉시 확인 가능

## Week 4 - Admission and Graduation

목표:

- 연간 이벤트 루프 완성

작업:

- 10월 입학 기준 설정 팝업 구현
- 3월 입학생 계산 구현
- 학과 개설 팝업 구현
- 학과별 학생 배치 로직 구현
- 2월 졸업 결과 계산 구현
- 졸업 결과 요약 UI 구현

완료 기준:

- 1년 플레이 시 입학과 졸업이 모두 정상 작동

## Week 5 - UI Polish and Save System

목표:

- 앱다운 완성도 확보

작업:

- AsyncStorage 저장 / 불러오기 구현
- 계절 배경 변경 적용
- 애니메이션 추가
- 귀여운 건물 아이콘 및 UI 에셋 반영
- 밸런스 1차 조정
- 온보딩 또는 짧은 도움말 추가

완료 기준:

- 앱 재실행 후 저장 데이터 복구 가능
- 전체 UI가 하나의 스타일로 정돈됨

## Week 6 - QA and Release Prep

목표:

- TestFlight 배포 및 심사 제출 준비

작업:

- iPhone 실기기 테스트
- 버그 수정
- 난이도 / 보상 수치 조정
- 앱 아이콘, 스플래시, 스크린샷 제작
- 개인정보 처리 관련 문구 정리
- App Store 소개문구 작성
- TestFlight 배포
- App Store Connect 메타데이터 입력

완료 기준:

- TestFlight에서 설치 및 플레이 가능
- 심사 제출에 필요한 자료가 준비됨

## Weekly Priorities

지켜야 할 우선순위:

1. 게임 루프 완성
2. 저장 기능 완성
3. 귀여운 UI 완성
4. 출시 자료 준비

버려도 되는 것:

- 과도한 연출
- 불필요한 설정 화면
- 고급 이벤트 시스템
- 안드로이드 대응

## Design and AI Workflow

매주 반복 작업:

1. Figma에서 다음 주 작업 화면 시안 작성
2. ChatGPT 이미지 생성으로 필요한 아이콘 또는 오브젝트 초안 생성
3. 실제 앱에 넣어 보고 크기와 색감 수정
4. 부족한 부분만 다시 생성

추천 제작 대상:

- 강의실 아이콘
- 기숙사 아이콘
- 연구소 아이콘
- 식당 아이콘
- 계절 배경 요소
- 마스코트 캐릭터

## Release Checklist

- Apple Developer 계정 준비
- App Store Connect 앱 생성
- 번들 아이디 확정
- 앱 이름 확정
- 앱 아이콘 제작
- 스크린샷 제작
- 설명문 / 키워드 작성
- 연령 등급 문항 작성
- 개인정보 수집 여부 확인

## Next Documents To Create

바로 이어서 만들면 좋은 문서:

- `game_balance_table.md`
- `ui_style_guide.md`
- `asset_prompt_pack.md`
- `app_store_submission_checklist.md`
