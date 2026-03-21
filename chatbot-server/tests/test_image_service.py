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
