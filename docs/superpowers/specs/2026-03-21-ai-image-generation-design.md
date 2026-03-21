# AI Image Generation for University Tycoon

## Overview

게임 이벤트(학교 생성, 건물 건설, 학과 개설) 발생 시 카카오 Karlo API로 AI 이미지를 즉시 생성하고, 카카오 챗봇 basicCard로 사용자에게 보여주는 기능.

## Decisions

| 항목 | 결정 | 근거 |
|------|------|------|
| 이미지 생성 서비스 | 카카오 Karlo API | 카카오 생태계 내, 무료 할당량, 한국어 지원 |
| 생성 시점 | 즉시 (동기) | 사용자 경험 — 액션 결과를 바로 확인 |
| 트리거 이벤트 | 게임 시작, 건물 건설, 학과 개설 | MVP 범위 최소화 |
| 카카오 응답 형태 | basicCard | 이미지 + 제목 + 설명 표준 카드 |
| 이미지 호스팅 | Karlo URL 직접 사용 | 가장 간단, 후에 영구 저장으로 전환 가능 |
| 프롬프트 전략 | 고정 프롬프트 + 계절 동적 반영 | 일관성 + 적절한 다양성 |
| 사진첩 | 후순위 (이번 스코프 제외) | MVP 집중 |

## Architecture

### Approach: GameEngine 통합

이미지 생성을 GameEngine 내부에서 처리. ImageService를 의존성 주입받아 사용.

```
GameEngine.build() / .start_game() / .department()
  → PromptBuilder.build(event_type, target, season)
  → ImageGenerator.generate(prompt)
  → GameResult(message=..., image_url=..., image_title=...)
  → KakaoAdapter: image_url 있으면 basicCard, 없으면 simpleText
```

대안으로 라우트 레이어에서 이미지 생성을 처리하는 방식(GameEngine을 순수하게 유지)도 고려했으나, GameEngine이 이미 비즈니스 로직의 중심이므로 이미지 생성도 게임 이벤트의 일부로 통합하는 것이 자연스럽다고 판단.

## Components

### 1. ImageGenerator Protocol (`services/image_service.py`)

```python
class ImageGenerator(Protocol):
    async def generate(self, prompt: str) -> str | None:
        """프롬프트로 이미지를 생성하고 URL을 반환. 실패 시 None."""
        ...

class KarloImageGenerator:
    """카카오 Karlo API를 사용한 이미지 생성."""

    def __init__(self, api_key: str, timeout: int = 10):
        ...

    async def generate(self, prompt: str) -> str | None:
        # POST https://api.kakaobrain.com/v2/inference/karlo/t2i
        # Authorization: KakaoAK {api_key}
        # 실패 시 None 반환 (게임 진행에 영향 없음)
        ...

class NullImageGenerator:
    """이미지 생성 비활성화. 항상 None 반환."""

    async def generate(self, prompt: str) -> str | None:
        return None
```

### 2. PromptBuilder (`services/image_service.py`)

고정 프롬프트 + 계절 suffix + 마스터 스타일 조합.

```python
MASTER_STYLE = "cute mobile tycoon game art, pastel palette, rounded toy-like shapes"
NEGATIVE_PROMPT = "realistic, photorealistic, dark, gritty, text, watermark"

BUILDING_PROMPTS = {
    "classroom": "university classroom building with large windows",
    "dormitory": "cozy student dormitory building",
    "laboratory": "modern science laboratory building",
    "cafeteria": "cheerful university cafeteria building",
}

DEPARTMENT_PROMPTS = {
    "art": "art studio with colorful paint splashes",
    "computer": "computer science building with digital screens",
    "medical": "medical school building with red cross",
    "humanities": "classic humanities library building",
}

START_GAME_PROMPT = "brand new small university campus, opening ceremony"

SEASON_SUFFIX = {
    "spring": "cherry blossoms, bright spring day",
    "summer": "green trees, sunny summer day",
    "autumn": "orange maple leaves, autumn atmosphere",
    "winter": "snow covered, cozy winter scene",
}
```

계절 판별은 기존 게임의 month 필드 사용:
- Spring: 3~5월
- Summer: 6~8월
- Autumn: 9~11월
- Winter: 12~2월

### 3. GameResult 확장 (`models/schemas.py`)

```python
class GameResult(BaseModel):
    message: str
    options: list[str] | None = None
    logs: list[str] | None = None
    image_url: str | None = None       # AI 생성 이미지 URL
    image_title: str | None = None     # basicCard 제목
```

### 4. KakaoAdapter basicCard 지원 (`services/kakao_adapter.py`)

```python
def to_kakao_response(result: GameResult) -> dict:
    outputs = []

    if result.image_url:
        outputs.append({
            "basicCard": {
                "title": result.image_title,
                "description": result.message,
                "thumbnail": {
                    "imageUrl": result.image_url
                }
            }
        })
    else:
        outputs.append({"simpleText": {"text": result.message}})

    # options, logs 처리는 기존과 동일
    ...
```

### 5. 설정 (`config.py`)

```python
karlo_api_key: str = ""              # UT_KARLO_API_KEY
image_generation_enabled: bool = True # UT_IMAGE_ENABLED
karlo_timeout: int = 10              # UT_KARLO_TIMEOUT (초)
```

### 6. 의존성 주입 (`main.py` 또는 `dependencies.py`)

```python
if settings.image_generation_enabled and settings.karlo_api_key:
    image_generator = KarloImageGenerator(settings.karlo_api_key, settings.karlo_timeout)
else:
    image_generator = NullImageGenerator()

game_engine = GameEngine(image_generator=image_generator)
```

## Timeout & Error Handling

### 카카오 Open Builder 응답 타임아웃 (5초)

Karlo API 응답이 3~10초 걸릴 수 있어 카카오 5초 타임아웃을 초과할 가능성이 있음.

**전략 (우선순위):**

1. **useCallback 활용** — 카카오 Open Builder의 callback 기능으로 즉시 "이미지 생성 중..." 응답 후, 이미지 준비 시 최종 응답 전송
2. **Graceful fallback** — useCallback 미지원/실패 시, 타임아웃 내에 이미지 생성 안 되면 텍스트만 응답

### API 에러 처리

- Karlo API 실패 → `image_url = None` → 텍스트만 응답 (게임 진행 정상)
- 네트워크 타임아웃 → 동일하게 fallback
- API 키 미설정 → `NullImageGenerator` 자동 사용
- 로깅: 실패 시 warning 레벨로 기록

## Future Extension Points

### ImageStorage Protocol (후순위)

```python
class ImageStorage(Protocol):
    async def save(self, image_url: str, user_id: str, event: str) -> str:
        """이미지를 저장하고 영구 URL을 반환."""
        ...

class PassthroughStorage:    # 지금: URL 그대로 반환
class S3Storage:             # 나중에: S3에 저장 후 영구 URL
```

지금은 `PassthroughStorage`만 구현. 나중에 사진첩/영구 저장 필요 시 `S3Storage` 등으로 교체.

### 사진첩 기능 (후순위)

- SaveState에 `images: list[ImageRecord]` 필드 추가
- 카카오 "사진첩 보기" 명령 → carousel 카드로 이미지 목록 표시
- ImageRecord: `{url, event_type, created_at, title}`

## Files to Create/Modify

| 파일 | 변경 |
|------|------|
| `services/image_service.py` | **신규** — ImageGenerator, KarloImageGenerator, NullImageGenerator, PromptBuilder |
| `models/schemas.py` | **수정** — GameResult에 image_url, image_title 추가 |
| `services/game_engine.py` | **수정** — ImageGenerator 주입, build/start_game/department에서 이미지 생성 호출 |
| `services/kakao_adapter.py` | **수정** — basicCard 렌더링 추가 |
| `config.py` | **수정** — Karlo API 설정 추가 |
| `main.py` 또는 `dependencies.py` | **수정** — ImageGenerator 의존성 주입 |
| `tests/test_image_service.py` | **신규** — PromptBuilder, NullImageGenerator 테스트 |
| `tests/test_kakao_adapter.py` | **신규** — basicCard 렌더링 테스트 |

## Non-Goals (이번 스코프 제외)

- 사진첩 기능
- 이미지 영구 저장 (S3 등)
- 모바일 앱 이미지 연동
- 턴 진행(advance-turn) 시 이미지 생성
- 이미지 스타일 사용자 커스터마이징
