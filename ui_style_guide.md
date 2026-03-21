# University Tycoon UI Style Guide

## 1. Purpose

이 문서는 `University Tycoon`의 시각 방향을 고정하기 위한 기준서다.

목표:

- 귀엽고 부드러운 모바일 게임 느낌 유지
- 숫자 정보가 많은 경영 게임이지만 화면이 딱딱해 보이지 않게 하기
- Figma 시안, React Native 구현, AI 에셋 생성이 같은 방향을 보게 하기

## 2. Visual Direction

### Core Mood

- 포근함
- 아기자기함
- 밝고 깨끗한 캠퍼스
- 과하게 유치하지 않은 캐주얼함

### Keywords

- cute
- pastel
- rounded
- cozy
- campus
- toy-like
- soft management sim

### Avoid

- 현실적인 대학 브랜딩 느낌
- 어두운 색 위주의 무거운 분위기
- 지나치게 화려한 네온
- 세밀한 3D 렌더 스타일
- 날카로운 모서리와 딱딱한 패널

## 3. Art Pillars

### 3.1 Friendly Shapes

- 카드, 버튼, 타일 모두 둥근 모서리를 사용
- 직사각형보다 말랑한 캡슐형과 라운드 박스를 우선
- 건물 아이콘도 네모반듯한 사실 묘사보다 장난감처럼 단순화

### 3.2 Soft Readability

- 배경은 밝고 넓게
- 정보 카드는 흰색 또는 아주 옅은 파스텔
- 글자는 남색 계열로 통일해 가독성 확보

### 3.3 Seasonal Warmth

- 계절에 따라 전체 배경 톤이 바뀌어야 함
- 봄: 연두 / 여름: 하늘 / 가을: 살구 / 겨울: 옅은 푸른 회색

## 4. Color System

현재 앱 기준 팔레트:

```ts
sky: #f5fbff
mint: #d8f3dc
cream: #fff7e8
peach: #ffd9c8
butter: #ffeaa6
lavender: #e7dcff
coral: #ff8f7a
navy: #29445d
slate: #62758a
white: #ffffff
border: #d7e4ee
spring: #e4f8d3
summer: #d8f1ff
autumn: #ffe2ba
winter: #eef3ff
arts: #ffb3c7
engineering: #9ed7ff
medical: #b7efc5
humanities: #f8d488
```

### Usage Rules

- 메인 CTA: `coral`
- 기본 배경: `sky`
- 카드 배경: `white`, `cream`
- 본문 텍스트: `navy`
- 보조 텍스트: `slate`
- 라인/경계: `border`
- 시스템 강조 태그:
  - 예체능: `arts`
  - 공학: `engineering`
  - 의학: `medical`
  - 기초학문: `humanities`

### Ratio

- 70% 밝은 중립 배경
- 20% 파스텔 포인트 컬러
- 10% 강조 색상과 CTA

## 5. Typography

### Tone

- 제목은 둥글고 통통한 느낌
- 본문은 작은 화면에서도 잘 읽혀야 함

### Figma Recommendation

- 헤드라인 후보:
  - `Baloo 2`
  - `Fredoka`
  - `Nunito`
- 본문 후보:
  - `Pretendard`
  - `Noto Sans KR`
  - `SUIT`

### App Recommendation

앱 구현 단계에서는 우선 시스템 폰트를 쓰되, Figma에서는 아래 조합을 권장:

- 제목: `Fredoka SemiBold`
- 본문: `Pretendard Medium / SemiBold`

### Type Scale

- Hero title: 28-32
- Section title: 20-22
- Card title: 14-16
- Body: 14-15
- Caption: 12-13

## 6. Components

### 6.1 Hero Card

- 큰 라운드 카드
- 상단 여백 넉넉하게
- 타이틀 + 서브텍스트 + CTA 구성
- 현재 월과 게임 정체성을 가장 먼저 보여줌

### 6.2 Info Card

- 짧은 데이터 요약 카드
- 좌상단 작은 컬러 바 또는 컬러 점 추가
- 한 카드에 정보 2-3줄만 넣기

### 6.3 Reputation Pill

- 짧고 통통한 캡슐형
- 색만 봐도 분야가 구분돼야 함
- 숫자와 라벨 간격 좁게 유지

### 6.4 Campus Tile

- 둥근 정사각형
- 빈 타일은 연한 반투명
- 건물 타일은 조금 더 따뜻한 배경
- 아이콘은 가운데 정렬

### 6.5 Bottom Modal

- 모바일 게임에 맞춰 하단 시트형
- 상단 모서리 크게 둥글게
- 옵션 카드는 크림색 배경으로 가볍게

## 7. Spacing and Radius

### Radius

- 메인 카드: 24-28
- 버튼: 16-18
- 작은 태그: 999
- 맵 타일: 16-18

### Spacing

- 화면 기본 패딩: 16
- 카드 내부 패딩: 14-20
- 카드 간격: 10-16
- 섹션 간격: 16-24

## 8. Icon Direction

### Style

- 플랫과 일러스트 중간
- 아주 얕은 음영
- 두꺼운 외곽선은 최소화
- 귀엽고 둥근 실루엣

### Asset Rules

- 하나의 아이콘 안에 요소를 너무 많이 넣지 않기
- 건물마다 실루엣 차이를 크게 만들기
- 정사각형 앱 화면에서 식별 가능해야 함
- 작은 크기에서도 무엇인지 보여야 함

### Building Personality

- 강의실: 따뜻한 지붕, 작은 창문, 깃발
- 기숙사: 포근한 집 느낌, 창문 강조
- 연구소: 둥근 돔 또는 플라스크 요소
- 식당: 밝은 간판, 귀여운 식기 상징

## 9. Motion Direction

### Principles

- 짧고 명확하게
- 화면이 튀지 않게
- 경영 게임 흐름을 방해하지 않게

### Suggested Motion

- 카드 진입: 아래에서 부드럽게 상승
- 버튼 탭: 0.96 정도로 살짝 눌림
- 월 진행: 배경 색상 천천히 전환
- 건설 완료: 타일이 살짝 튀는 피드백

## 10. Screen Direction

### Main Game Screen

- 상단: 연월, 게임 설명, 메인 버튼
- 중단: 예산/명성/학생/운영능력 카드
- 그 아래: 분야 태그와 액션 버튼
- 하단: 캠퍼스 맵과 로그

### Admission Popup

- 복잡한 표보다 과목별 스텝퍼 UI
- 학부모/학생 대상 입시표가 아니라 귀여운 게임 메뉴처럼 보이게

### Department Popup

- 학과 카드마다 분야 색상을 아주 약하게 섞기
- 잠금 상태보다 `아직 미개설` 느낌으로 표현

## 11. Figma Workflow

### Must Make First

- 메인 화면
- 건설 팝업
- 학과 개설 팝업
- 입학 기준 팝업
- 월 결과 팝업

### Recommended Layers

- `Foundations / Colors`
- `Foundations / Type`
- `Components / Cards`
- `Components / Buttons`
- `Components / Pills`
- `Screens / Main`
- `Screens / Popups`

### Practical Rule

- 피그마에서 먼저 예쁘게만 만들지 말고, React Native로 바로 옮길 수 있는 카드 구조로 설계

## 12. Quality Checklist

- 한 화면에 강한 색이 3개 이상 경쟁하지 않는가
- 제목과 버튼이 충분히 눈에 띄는가
- 숫자 카드가 읽기 쉬운가
- 건물 아이콘이 작아도 구분되는가
- 파스텔만 쓰다가 흐릿해지지 않았는가
- 귀엽지만 너무 유아용처럼 보이지는 않는가
