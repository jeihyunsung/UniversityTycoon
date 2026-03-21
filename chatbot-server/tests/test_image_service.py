from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.in_memory import InMemorySaveRepository
from app.services.game_engine import GameEngine
from app.services.image_service import (
    MASTER_STYLE,
    NEGATIVE_PROMPT,
    KarloImageGenerator,
    NullImageGenerator,
    PromptBuilder,
    _get_season,
)
from tests.conftest import make_webhook


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


@pytest.mark.asyncio
async def test_null_image_generator_returns_none() -> None:
    gen = NullImageGenerator()
    result = await gen.generate("any prompt", "any negative")
    assert result is None


class TestKarloImageGenerator:
    @pytest.mark.asyncio
    async def test_generate_returns_image_url(self) -> None:
        karlo = KarloImageGenerator(api_key="test-key", timeout=4)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "abc",
            "model_version": "v2.1",
            "images": [{"id": "img1", "image": "https://example.com/image.png"}],
        }
        mock_response.raise_for_status = MagicMock()

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
