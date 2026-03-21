"""AI image generation service for University Tycoon."""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

KARLO_API_URL = "https://api.kakaobrain.com/v2/inference/karlo/t2i"


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


class ImageGenerator(Protocol):
    """Interface for AI image generation services."""

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        """Generate an image and return its URL. Returns None on failure."""
        ...


class NullImageGenerator:
    """No-op image generator. Always returns None."""

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        return None


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
