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
| HTTP 클라이언트 | httpx (async) | FastAPI와 호환, 비동기 논블로킹 |
| 타임아웃 전략 | Graceful fallback (MVP) | useCallback은 후순위로 |

## Architecture

### Approach: GameEngine 통합

이미지 생성을 GameEngine 내부에서 처리. ImageService를 의존성 주입받아 사용.

```
GameEngine.build() / .start_game() / .department()
  → PromptBuilder.build(event_type, target, month)
     → (prompt, negative_prompt) 튜플 반환
  → ImageGenerator.generate(prompt, negative_prompt)
  → GameResult(message=..., image_url=..., image_title=...)
  → KakaoAdapter: image_url 있으면 basicCard, 없으면 simpleText
```

대안으로 라우트 레이어에서 이미지 생성을 처리하는 방식(GameEngine을 순수하게 유지)도 고려했으나, GameEngine이 이미 비즈니스 로직의 중심이므로 이미지 생성도 게임 이벤트의 일부로 통합하는 것이 자연스럽다고 판단.

### Prerequisites: GameEngine 리팩토링

현재 GameEngine은 `__init__` 없이 모듈 레벨 싱글턴으로 사용 중:
```python
# 현재
game_engine = GameEngine()
# 라우트에서 직접 import
from app.services.game_engine import game_engine
```

변경 필요:
1. `GameEngine.__init__(self, image_generator: ImageGenerator)` 추가
2. `game_engine` 싱글턴을 `main.py`에서 설정에 따라 생성
3. 라우트에서 FastAPI dependency injection으로 `GameEngine` 주입

## Components

### 1. ImageGenerator Protocol (`app/services/image_service.py`)

```python
from typing import Protocol

class ImageGenerator(Protocol):
    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        """프롬프트로 이미지를 생성하고 URL을 반환. 실패 시 None."""
        ...

class KarloImageGenerator:
    """카카오 Karlo API를 사용한 이미지 생성. httpx.AsyncClient 사용."""

    def __init__(self, api_key: str, timeout: int = 10):
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        # httpx.AsyncClient 사용 (논블로킹)
        # POST https://api.kakaobrain.com/v2/inference/karlo/t2i
        # Headers: Authorization: KakaoAK {api_key}, Content-Type: application/json
        # Body: {"version": "v2.1", "prompt": prompt, "negative_prompt": negative_prompt,
        #        "width": 512, "height": 512, "samples": 1}
        # Response: {"id": "...", "model_version": "...", "images": [{"id": "...", "image": "<URL>"}]}
        # 반환: response["images"][0]["image"]
        # 실패 시 warning 로깅 후 None 반환
        ...

class NullImageGenerator:
    """이미지 생성 비활성화. 항상 None 반환."""

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        return None
```

### 2. PromptBuilder (`app/services/image_service.py`)

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

def _get_season(month: int) -> str:
    """월(1-12)에서 계절 문자열 반환."""
    if month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    elif month in (9, 10, 11):
        return "autumn"
    else:
        return "winter"


class PromptBuilder:
    @staticmethod
    def build(event_type: str, target: str, month: int) -> tuple[str, str]:
        """이벤트와 컨텍스트로 (prompt, negative_prompt) 튜플을 조합.

        Args:
            event_type: "start_game", "building", "department"
            target: 건물/학과 ID (예: "classroom", "art"). start_game일 때는 무시.
            month: 현재 게임 월 (1-12)

        Returns:
            (prompt, negative_prompt) 튜플
        """
        season = _get_season(month)
        season_text = SEASON_SUFFIX[season]

        if event_type == "start_game":
            subject = START_GAME_PROMPT
        elif event_type == "building":
            subject = BUILDING_PROMPTS[target]
        elif event_type == "department":
            subject = DEPARTMENT_PROMPTS[target]
        else:
            subject = target

        prompt = f"{subject}, {season_text}, {MASTER_STYLE}"
        return (prompt, NEGATIVE_PROMPT)
```

### 3. GameResult 확장 (`app/models/schemas.py`)

기존 GameResult 모델에 2개 필드만 추가:

```python
class GameResult(BaseModel):
    # 기존 필드 유지
    ok: bool = True
    message: str
    quick_replies: list[str] = Field(default_factory=list, alias="quickReplies")
    logs: list[str] = Field(default_factory=list)
    options: list[dict[str, Any]] = Field(default_factory=list)
    error_code: str | None = Field(default=None, alias="errorCode")
    save: SaveState | None = None
    # 신규 필드
    image_url: str | None = Field(default=None, alias="imageUrl")
    image_title: str | None = Field(default=None, alias="imageTitle")
```

### 4. KakaoAdapter basicCard 지원 (`app/services/kakao_adapter.py`)

`basicCard` 사용 시 description은 최대 230자로 제한.

```python
def to_kakao_response(result: GameResult) -> dict:
    outputs = []

    if result.image_url:
        description = result.message[:230]  # basicCard 글자 수 제한
        outputs.append({
            "basicCard": {
                "title": result.image_title or "",
                "description": description,
                "thumbnail": {
                    "imageUrl": result.image_url
                }
            }
        })
    else:
        outputs.append({"simpleText": {"text": result.message}})

    # options, logs, quickReplies 처리는 기존과 동일
    ...
```

### 5. 설정 (`app/config.py`)

```python
karlo_api_key: str = ""              # UT_KARLO_API_KEY
image_generation_enabled: bool = True # UT_IMAGE_ENABLED
karlo_timeout: int = 10              # UT_KARLO_TIMEOUT (초)
```

### 6. 의존성 주입 (`app/main.py`)

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

**MVP 전략: Graceful fallback**

- Karlo API 호출에 타임아웃(4초)을 설정하여 카카오 5초 제한 내에 응답
- 4초 내에 이미지 생성 실패 시 `image_url = None` → 텍스트만 응답
- 이미지 생성 지연이 게임 진행을 방해하지 않음

**후순위: useCallback 활용**

카카오 Open Builder의 callback 기능으로 즉시 "이미지 생성 중..." 응답 후, 이미지 준비 시 최종 응답 전송. 이 방식은 별도의 callback 엔드포인트와 백그라운드 태스크 인프라가 필요하므로 MVP 이후에 구현.

### API 에러 처리

- Karlo API 실패 → `image_url = None` → 텍스트만 응답 (게임 진행 정상)
- 네트워크 타임아웃 → 동일하게 fallback
- API 키 미설정 → `NullImageGenerator` 자동 사용
- 로깅: 실패 시 warning 레벨로 기록 (`logging.warning`)

## Dependencies

`pyproject.toml`에 추가:
- `httpx` — Karlo API 비동기 HTTP 호출

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

### useCallback 지원 (후순위)

카카오 Open Builder callback을 활용해 이미지 생성 시간 제약 해소. 별도 설계 필요.

### 사진첩 기능 (후순위)

- SaveState에 `images: list[ImageRecord]` 필드 추가
- 카카오 "사진첩 보기" 명령 → carousel 카드로 이미지 목록 표시
- ImageRecord: `{url, event_type, created_at, title}`

## Files to Create/Modify

| 파일 | 변경 |
|------|------|
| `chatbot-server/app/services/image_service.py` | **신규** — ImageGenerator Protocol, KarloImageGenerator, NullImageGenerator, PromptBuilder, `_get_season()` |
| `chatbot-server/app/models/schemas.py` | **수정** — GameResult에 `image_url`, `image_title` 필드 추가 |
| `chatbot-server/app/services/game_engine.py` | **수정** — `__init__`에 ImageGenerator 주입, `build`/`start_game`/`department`에서 PromptBuilder + ImageGenerator 호출 |
| `chatbot-server/app/services/kakao_adapter.py` | **수정** — `to_kakao_response`에 basicCard 렌더링 분기 추가 |
| `chatbot-server/app/config.py` | **수정** — `karlo_api_key`, `image_generation_enabled`, `karlo_timeout` 추가 |
| `chatbot-server/app/main.py` | **수정** — ImageGenerator 인스턴스 생성, GameEngine에 주입 |
| `chatbot-server/pyproject.toml` | **수정** — `httpx` 의존성 추가 |
| `chatbot-server/tests/test_image_service.py` | **신규** — PromptBuilder 조합 테스트, _get_season 테스트, NullImageGenerator 테스트 |
| `chatbot-server/tests/test_kakao_adapter.py` | **신규** — basicCard 렌더링 테스트 (image_url 있을 때/없을 때), description 230자 제한 테스트 |

## Test Strategy

### test_image_service.py
- `_get_season()`: 각 월별 올바른 계절 반환 확인
- `PromptBuilder.build()`: 각 event_type/target/month 조합에 대한 프롬프트 조합 검증
- `PromptBuilder.build()`: 반환값이 `(prompt, negative_prompt)` 튜플인지 확인
- `NullImageGenerator.generate()`: 항상 None 반환 확인
- `KarloImageGenerator`: httpx mock으로 API 호출/파싱/에러 처리 테스트

### test_kakao_adapter.py
- `image_url` 있을 때 basicCard 구조 검증
- `image_url` 없을 때 기존 simpleText 동작 유지
- `description` 230자 초과 시 truncation 확인
- `image_title`이 None일 때 빈 문자열 처리

## Non-Goals (이번 스코프 제외)

- 사진첩 기능
- 이미지 영구 저장 (S3 등)
- 모바일 앱 이미지 연동
- 턴 진행(advance-turn) 시 이미지 생성
- 이미지 스타일 사용자 커스터마이징
- useCallback 기반 비동기 이미지 전달
