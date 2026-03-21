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


from app.services.image_service import NullImageGenerator


@pytest.mark.asyncio
async def test_null_image_generator_returns_none() -> None:
    gen = NullImageGenerator()
    result = await gen.generate("any prompt", "any negative")
    assert result is None


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
