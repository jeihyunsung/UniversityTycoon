# AI Image Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate AI images via Karlo API when game events occur (start game, build, open department) and display them as Kakao basicCard responses.

**Architecture:** ImageGenerator Protocol with Karlo/Null implementations, injected into GameEngine. PromptBuilder composes prompts from fixed templates + season suffix. KakaoAdapter renders basicCard when image_url is present.

**Tech Stack:** Python 3.11+, FastAPI, httpx (async), Karlo API, Pydantic

**Spec:** `docs/superpowers/specs/2026-03-21-ai-image-generation-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `chatbot-server/app/services/image_service.py` | Create | ImageGenerator Protocol, KarloImageGenerator, NullImageGenerator, PromptBuilder, `_get_season()` |
| `chatbot-server/app/models/schemas.py` | Modify | Add `image_url`, `image_title` fields to GameResult |
| `chatbot-server/app/services/kakao_adapter.py` | Modify | Add basicCard rendering when image_url present |
| `chatbot-server/app/config.py` | Modify | Add Karlo API settings |
| `chatbot-server/app/services/game_engine.py` | Modify | Accept ImageGenerator, call it in start_game/build/department |
| `chatbot-server/app/api/deps.py` | Modify | Provide ImageGenerator via DI |
| `chatbot-server/app/main.py` | Modify | Create ImageGenerator instance at startup |
| `chatbot-server/pyproject.toml` | Modify | (httpx already in dev deps — move to runtime) |
| `chatbot-server/tests/test_image_service.py` | Create | PromptBuilder, _get_season, NullImageGenerator tests |
| `chatbot-server/tests/test_kakao_adapter.py` | Create | basicCard rendering tests |
| `chatbot-server/tests/conftest.py` | Modify | Update engine fixture to pass NullImageGenerator |

---

### Task 1: PromptBuilder and _get_season

**Files:**
- Create: `chatbot-server/app/services/image_service.py`
- Create: `chatbot-server/tests/test_image_service.py`

- [ ] **Step 1: Write failing tests for `_get_season`**

```python
# tests/test_image_service.py
import pytest

from app.services.image_service import _get_season


@pytest.mark.parametrize(
    "month, expected",
    [
        (3, "spring"), (4, "spring"), (5, "spring"),
        (6, "summer"), (7, "summer"), (8, "summer"),
        (9, "autumn"), (10, "autumn"), (11, "autumn"),
        (12, "winter"), (1, "winter"), (2, "winter"),
    ],
)
def test_get_season(month: int, expected: str) -> None:
    assert _get_season(month) == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::test_get_season -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.image_service'`

- [ ] **Step 3: Implement `_get_season` in image_service.py**

```python
# app/services/image_service.py
"""AI image generation service for University Tycoon."""

from __future__ import annotations


def _get_season(month: int) -> str:
    """Return season string from month (1-12)."""
    if month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    elif month in (9, 10, 11):
        return "autumn"
    else:
        return "winter"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::test_get_season -v`
Expected: PASS

- [ ] **Step 5: Write failing tests for PromptBuilder**

Append to `tests/test_image_service.py`:

```python
from app.services.image_service import PromptBuilder, MASTER_STYLE, NEGATIVE_PROMPT


class TestPromptBuilder:
    def test_building_prompt_contains_subject_and_style(self) -> None:
        prompt, neg = PromptBuilder.build("building", "classroom", 4)
        assert "classroom" in prompt
        assert MASTER_STYLE in prompt
        assert "cherry blossoms" in prompt  # spring
        assert neg == NEGATIVE_PROMPT

    def test_department_prompt(self) -> None:
        prompt, neg = PromptBuilder.build("department", "art", 7)
        assert "art studio" in prompt
        assert "sunny summer" in prompt
        assert neg == NEGATIVE_PROMPT

    def test_start_game_prompt(self) -> None:
        prompt, neg = PromptBuilder.build("start_game", "", 3)
        assert "university campus" in prompt
        assert neg == NEGATIVE_PROMPT

    def test_winter_season_suffix(self) -> None:
        prompt, _ = PromptBuilder.build("building", "dormitory", 12)
        assert "snow" in prompt
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::TestPromptBuilder -v`
Expected: FAIL — `ImportError: cannot import name 'PromptBuilder'`

- [ ] **Step 7: Implement PromptBuilder, constants, and prompt dicts**

Add to `app/services/image_service.py`:

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


class PromptBuilder:
    """Composes image generation prompts from event context."""

    @staticmethod
    def build(event_type: str, target: str, month: int) -> tuple[str, str]:
        """Build (prompt, negative_prompt) tuple from event context.

        Args:
            event_type: "start_game", "building", or "department".
            target: Building/department ID. Ignored for start_game.
            month: Current game month (1-12).

        Returns:
            Tuple of (prompt, negative_prompt).
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

- [ ] **Step 8: Run all tests to verify they pass**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add chatbot-server/app/services/image_service.py chatbot-server/tests/test_image_service.py
git commit -m "feat: add PromptBuilder and _get_season for image generation"
```

---

### Task 2: ImageGenerator Protocol and NullImageGenerator

**Files:**
- Modify: `chatbot-server/app/services/image_service.py`
- Modify: `chatbot-server/tests/test_image_service.py`

- [ ] **Step 1: Write failing test for NullImageGenerator**

Append to `tests/test_image_service.py`:

```python
from app.services.image_service import NullImageGenerator


@pytest.mark.asyncio
async def test_null_image_generator_returns_none() -> None:
    gen = NullImageGenerator()
    result = await gen.generate("any prompt", "any negative")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::test_null_image_generator_returns_none -v`
Expected: FAIL — `ImportError: cannot import name 'NullImageGenerator'`

- [ ] **Step 3: Implement ImageGenerator Protocol and NullImageGenerator**

Add to `app/services/image_service.py`:

```python
from typing import Protocol


class ImageGenerator(Protocol):
    """Interface for AI image generation services."""

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        """Generate an image and return its URL. Returns None on failure."""
        ...


class NullImageGenerator:
    """No-op image generator. Always returns None."""

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::test_null_image_generator_returns_none -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add chatbot-server/app/services/image_service.py chatbot-server/tests/test_image_service.py
git commit -m "feat: add ImageGenerator protocol and NullImageGenerator"
```

---

### Task 3: KarloImageGenerator

**Files:**
- Modify: `chatbot-server/app/services/image_service.py`
- Modify: `chatbot-server/tests/test_image_service.py`
- Modify: `chatbot-server/pyproject.toml`

- [ ] **Step 1: Move httpx from dev to runtime deps in pyproject.toml**

In `chatbot-server/pyproject.toml`, move `httpx>=0.27` from `[project.optional-dependencies] dev` to `[project] dependencies`.

- [ ] **Step 2: Write failing test for KarloImageGenerator (success case)**

Append to `tests/test_image_service.py`:

```python
from unittest.mock import AsyncMock, patch

from app.services.image_service import KarloImageGenerator


class TestKarloImageGenerator:
    @pytest.mark.asyncio
    async def test_generate_returns_image_url(self) -> None:
        karlo = KarloImageGenerator(api_key="test-key", timeout=4)
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "abc",
            "model_version": "v2.1",
            "images": [{"id": "img1", "image": "https://example.com/image.png"}],
        }
        mock_response.raise_for_status = AsyncMock()

        with patch("app.services.image_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = await karlo.generate("test prompt", "negative")

        assert result == "https://example.com/image.png"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_returns_none_on_error(self) -> None:
        karlo = KarloImageGenerator(api_key="test-key", timeout=4)

        with patch("app.services.image_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = Exception("Network error")
            mock_client_cls.return_value = mock_client

            result = await karlo.generate("test prompt")

        assert result is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::TestKarloImageGenerator -v`
Expected: FAIL — `ImportError: cannot import name 'KarloImageGenerator'`

- [ ] **Step 4: Implement KarloImageGenerator**

Add to `app/services/image_service.py`:

```python
import logging

import httpx

logger = logging.getLogger(__name__)

KARLO_API_URL = "https://api.kakaobrain.com/v2/inference/karlo/t2i"


class KarloImageGenerator:
    """Image generator using Kakao Karlo API."""

    def __init__(self, api_key: str, timeout: int = 4) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        """Call Karlo API and return the generated image URL."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    KARLO_API_URL,
                    headers={
                        "Authorization": f"KakaoAK {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "version": "v2.1",
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "width": 512,
                        "height": 512,
                        "samples": 1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["images"][0]["image"]
        except Exception:
            logger.warning("Karlo image generation failed", exc_info=True)
            return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add chatbot-server/app/services/image_service.py chatbot-server/tests/test_image_service.py chatbot-server/pyproject.toml
git commit -m "feat: add KarloImageGenerator with httpx async client"
```

---

### Task 4: Extend GameResult with image fields

**Files:**
- Modify: `chatbot-server/app/models/schemas.py`

- [ ] **Step 1: Add image_url and image_title to GameResult**

In `chatbot-server/app/models/schemas.py`, add two fields to `GameResult` after the `save` field:

```python
    image_url: str | None = Field(default=None, alias="imageUrl")
    image_title: str | None = Field(default=None, alias="imageTitle")
```

- [ ] **Step 2: Run existing tests to verify nothing breaks**

Run: `cd chatbot-server && python -m pytest -v`
Expected: All existing tests PASS (new fields have defaults)

- [ ] **Step 3: Commit**

```bash
git add chatbot-server/app/models/schemas.py
git commit -m "feat: add image_url and image_title fields to GameResult"
```

---

### Task 5: KakaoAdapter basicCard rendering

**Files:**
- Modify: `chatbot-server/app/services/kakao_adapter.py`
- Create: `chatbot-server/tests/test_kakao_adapter.py`

- [ ] **Step 1: Write failing tests for basicCard rendering**

Note: The existing `GameResult` uses aliases (`quickReplies`, `errorCode`) in constructors. Since `populate_by_name` is not set, use alias names (`imageUrl`, `imageTitle`) when constructing GameResult in tests.

```python
# tests/test_kakao_adapter.py
from app.models.schemas import GameResult
from app.services.kakao_adapter import to_kakao_response


class TestBasicCardRendering:
    def test_image_url_renders_basic_card(self) -> None:
        result = GameResult(
            message="강의동 건설 완료!",
            imageUrl="https://example.com/img.png",
            imageTitle="🎉 강의동 건설!",
        )
        resp = to_kakao_response(result)
        outputs = resp["template"]["outputs"]
        card = outputs[0]["basicCard"]
        assert card["title"] == "🎉 강의동 건설!"
        assert card["thumbnail"]["imageUrl"] == "https://example.com/img.png"
        assert card["description"] == "강의동 건설 완료!"

    def test_no_image_renders_simple_text(self) -> None:
        result = GameResult(message="현재 상태입니다.")
        resp = to_kakao_response(result)
        outputs = resp["template"]["outputs"]
        assert "simpleText" in outputs[0]
        assert outputs[0]["simpleText"]["text"] == "현재 상태입니다."

    def test_description_truncated_at_230_chars(self) -> None:
        long_msg = "가" * 300
        result = GameResult(
            message=long_msg,
            imageUrl="https://example.com/img.png",
            imageTitle="제목",
        )
        resp = to_kakao_response(result)
        card = resp["template"]["outputs"][0]["basicCard"]
        assert len(card["description"]) == 230

    def test_image_title_none_defaults_to_empty(self) -> None:
        result = GameResult(
            message="테스트",
            imageUrl="https://example.com/img.png",
        )
        resp = to_kakao_response(result)
        card = resp["template"]["outputs"][0]["basicCard"]
        assert card["title"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd chatbot-server && python -m pytest tests/test_kakao_adapter.py -v`
Expected: FAIL — basicCard not rendered (simpleText used instead)

- [ ] **Step 3: Modify kakao_adapter.py to support basicCard**

Read current `chatbot-server/app/services/kakao_adapter.py` and modify `to_kakao_response()`:

Replace the first line that builds simpleText output with a conditional:

```python
def to_kakao_response(result: GameResult) -> dict:
    outputs: list[dict] = []

    if result.image_url:
        outputs.append({
            "basicCard": {
                "title": result.image_title or "",
                "description": result.message[:230],
                "thumbnail": {
                    "imageUrl": result.image_url,
                },
            }
        })
    else:
        outputs.append({"simpleText": {"text": result.message}})

    # Rest of function unchanged (options, logs, quickReplies)
    ...
```

Keep the existing options/logs/quickReplies handling after the conditional.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd chatbot-server && python -m pytest tests/test_kakao_adapter.py -v`
Expected: All PASS

- [ ] **Step 5: Run all tests to check for regressions**

Run: `cd chatbot-server && python -m pytest -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add chatbot-server/app/services/kakao_adapter.py chatbot-server/tests/test_kakao_adapter.py
git commit -m "feat: add basicCard rendering to KakaoAdapter for image responses"
```

---

### Task 6: Config settings for Karlo API

**Files:**
- Modify: `chatbot-server/app/config.py`

- [ ] **Step 1: Add Karlo settings to Settings class**

In `chatbot-server/app/config.py`, add three fields to the `Settings` class:

```python
    karlo_api_key: str = ""
    image_generation_enabled: bool = True
    karlo_timeout: int = 4
```

These will map to env vars `UT_KARLO_API_KEY`, `UT_IMAGE_GENERATION_ENABLED`, `UT_KARLO_TIMEOUT` via the existing `env_prefix = "UT_"`.

- [ ] **Step 2: Run existing tests to verify nothing breaks**

Run: `cd chatbot-server && python -m pytest -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add chatbot-server/app/config.py
git commit -m "feat: add Karlo API configuration settings"
```

---

### Task 7: Integrate ImageGenerator into GameEngine

**Files:**
- Modify: `chatbot-server/app/services/game_engine.py`
- Modify: `chatbot-server/tests/conftest.py`
- Modify: `chatbot-server/tests/test_image_service.py`

This is the core integration step. GameEngine needs to:
1. Accept an `ImageGenerator` in `__init__`
2. Call `PromptBuilder.build()` + `ImageGenerator.generate()` in `start_game`, `build`, `department`
3. Set `image_url` and `image_title` on the returned `GameResult`

- [ ] **Step 1: Write failing integration test**

Append to `tests/test_image_service.py`. Reuse existing `make_webhook` from `conftest.py`. Note: GameEngine methods take `(request, repo)` order, not `(repo, request)`. Use correct param key `buildingType` or action names like `ACTION_BUILD_CLASSROOM`. Use aliases (`imageUrl`, `imageTitle`) when checking GameResult fields via attribute access (`.image_url`/`.image_title` works for reading).

```python
from app.services.game_engine import GameEngine
from app.repositories.in_memory import InMemorySaveRepository
from tests.conftest import make_webhook


class TestGameEngineImageIntegration:
    @pytest.mark.asyncio
    async def test_start_game_sets_image_url_with_generator(self) -> None:
        mock_gen = AsyncMock()
        mock_gen.generate.return_value = "https://example.com/campus.png"
        engine = GameEngine(image_generator=mock_gen)
        repo = InMemorySaveRepository()

        webhook = make_webhook("test-user")
        result = await engine.start_game(webhook, repo)

        assert result.image_url == "https://example.com/campus.png"
        assert result.image_title is not None
        mock_gen.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_sets_image_url(self) -> None:
        mock_gen = AsyncMock()
        mock_gen.generate.return_value = "https://example.com/classroom.png"
        engine = GameEngine(image_generator=mock_gen)
        repo = InMemorySaveRepository()

        webhook = make_webhook("test-user")
        await engine.start_game(webhook, repo)
        build_webhook = make_webhook("test-user", action_name="ACTION_BUILD_CLASSROOM")
        result = await engine.build(build_webhook, repo)

        assert result.image_url == "https://example.com/classroom.png"

    @pytest.mark.asyncio
    async def test_department_sets_image_url(self) -> None:
        mock_gen = AsyncMock()
        mock_gen.generate.return_value = "https://example.com/art.png"
        engine = GameEngine(image_generator=mock_gen)
        repo = InMemorySaveRepository()

        webhook = make_webhook("test-user")
        await engine.start_game(webhook, repo)
        dept_webhook = make_webhook("test-user", action_name="ACTION_DEPT_ART")
        result = await engine.department(dept_webhook, repo)

        assert result.image_url == "https://example.com/art.png"

    @pytest.mark.asyncio
    async def test_build_works_when_image_generation_fails(self) -> None:
        mock_gen = AsyncMock()
        mock_gen.generate.return_value = None
        engine = GameEngine(image_generator=mock_gen)
        repo = InMemorySaveRepository()

        webhook = make_webhook("test-user")
        await engine.start_game(webhook, repo)
        build_webhook = make_webhook("test-user", action_name="ACTION_BUILD_CLASSROOM")
        result = await engine.build(build_webhook, repo)

        assert result.ok is True
        assert result.image_url is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::TestGameEngineImageIntegration -v`
Expected: FAIL — `GameEngine.__init__() got an unexpected keyword argument 'image_generator'`

- [ ] **Step 3: Modify GameEngine to accept and use ImageGenerator**

In `chatbot-server/app/services/game_engine.py`:

1. Add import at top:
```python
from app.services.image_service import ImageGenerator, NullImageGenerator, PromptBuilder
```

2. Add `__init__` to `GameEngine` class:
```python
    def __init__(self, image_generator: ImageGenerator | None = None) -> None:
        self._image_gen = image_generator or NullImageGenerator()
```

3. In `start_game()`, after creating the save and before returning the GameResult, add image generation:
```python
        prompt, neg = PromptBuilder.build("start_game", "", save.month)
        image_url = await self._image_gen.generate(prompt, neg)
```
Then add `imageUrl=image_url` and `imageTitle="🎓 대학교 설립!"` to the returned GameResult constructor. (Use alias names to match existing code convention — e.g. `quickReplies=...`)

4. In `build()`, after successful building (where `ok=True` result is returned), add:
```python
        prompt, neg = PromptBuilder.build("building", building_type, save.month)
        image_url = await self._image_gen.generate(prompt, neg)
```
Then add `imageUrl=image_url` and `imageTitle=f"🏗️ {definition.label} 건설!"` to the returned GameResult constructor.

5. In `department()`, after successful opening, add:
```python
        prompt, neg = PromptBuilder.build("department", dept_id, save.month)
        image_url = await self._image_gen.generate(prompt, neg)
```
Then add `imageUrl=image_url` and `imageTitle=f"📚 {dept.label} 개설!"` to the returned GameResult constructor.

6. Update the module-level singleton:
```python
game_engine = GameEngine()  # Uses NullImageGenerator by default
```

- [ ] **Step 4: Update conftest.py engine fixture**

In `chatbot-server/tests/conftest.py`, update the `engine` fixture to explicitly pass `NullImageGenerator`:

```python
from app.services.image_service import NullImageGenerator

@pytest.fixture
def engine() -> GameEngine:
    return GameEngine(image_generator=NullImageGenerator())
```

- [ ] **Step 5: Run integration tests to verify they pass**

Run: `cd chatbot-server && python -m pytest tests/test_image_service.py::TestGameEngineImageIntegration -v`
Expected: All PASS

- [ ] **Step 6: Run all tests to check for regressions**

Run: `cd chatbot-server && python -m pytest -v`
Expected: All PASS (existing tests use NullImageGenerator, image_url defaults to None)

- [ ] **Step 7: Commit**

```bash
git add chatbot-server/app/services/game_engine.py chatbot-server/tests/conftest.py chatbot-server/tests/test_image_service.py
git commit -m "feat: integrate ImageGenerator into GameEngine for start/build/department"
```

---

### Task 8: Wire up dependency injection in main.py

**Files:**
- Modify: `chatbot-server/app/main.py`
- Modify: `chatbot-server/app/api/deps.py`
- Modify: `chatbot-server/app/api/routes/kakao.py`

- [ ] **Step 1: Update main.py to create ImageGenerator at startup**

In `chatbot-server/app/main.py`, in the `lifespan()` context manager, create the ImageGenerator based on settings and store it in `app.state`:

```python
from app.services.image_service import KarloImageGenerator, NullImageGenerator
from app.services.game_engine import GameEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Existing DB setup...

    # Image generator setup
    if settings.image_generation_enabled and settings.karlo_api_key:
        image_gen = KarloImageGenerator(settings.karlo_api_key, settings.karlo_timeout)
    else:
        image_gen = NullImageGenerator()

    app.state.game_engine = GameEngine(image_generator=image_gen)

    yield
```

- [ ] **Step 2: Add `get_game_engine` dependency in deps.py**

In `chatbot-server/app/api/deps.py`, add a dependency function:

```python
from fastapi import Request
from app.services.game_engine import GameEngine

def get_game_engine(request: Request) -> GameEngine:
    return request.app.state.game_engine
```

- [ ] **Step 3: Update routes to use injected GameEngine**

In `chatbot-server/app/api/routes/kakao.py`:
- Remove: `from app.services.game_engine import game_engine`
- Add: `from app.api.deps import get_game_engine`
- Add `game_engine: GameEngine = Depends(get_game_engine)` parameter to each endpoint
- Replace the module-level `game_engine` reference with the injected parameter

- [ ] **Step 4: Run all tests to verify**

Run: `cd chatbot-server && python -m pytest -v`
Expected: All PASS. Note: test_api.py tests use TestClient which creates the app, so the lifespan will run with NullImageGenerator (no API key set in test env).

- [ ] **Step 5: Commit**

```bash
git add chatbot-server/app/main.py chatbot-server/app/api/deps.py chatbot-server/app/api/routes/kakao.py
git commit -m "feat: wire ImageGenerator dependency injection via FastAPI lifespan"
```

---

### Task 9: Final verification and cleanup

- [ ] **Step 1: Run full test suite**

Run: `cd chatbot-server && python -m pytest -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Verify module imports are clean**

Run: `cd chatbot-server && python -c "from app.services.image_service import ImageGenerator, KarloImageGenerator, NullImageGenerator, PromptBuilder; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Remove module-level game_engine singleton**

After Task 8, routes no longer import the module-level `game_engine` singleton from `game_engine.py` (line 418). Remove the `game_engine = GameEngine()` line at the bottom of `game_engine.py`. Verify no remaining imports reference it:

Run: `cd chatbot-server && grep -r "from app.services.game_engine import game_engine" --include="*.py"`
Expected: No matches

- [ ] **Step 4: Commit any cleanup**

```bash
git add -A
git commit -m "chore: final cleanup for AI image generation feature"
```
