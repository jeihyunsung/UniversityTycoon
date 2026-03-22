"""AI image generation service for University Tycoon."""

from __future__ import annotations

import logging
from typing import Protocol

import time

import httpx

logger = logging.getLogger(__name__)


MASTER_STYLE = "3D isometric anime style, ornate and lavish university building, rich details, vibrant colors, dramatic lighting, small centered building with very large empty sky and ground margins, zoomed out, lots of negative space around the building"
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
            subject = BUILDING_PROMPTS.get(target, target)
        elif event_type == "department":
            subject = DEPARTMENT_PROMPTS.get(target, target)
        else:
            subject = target

        prompt = f"{subject}, {season_text}, {MASTER_STYLE}"
        return (prompt, NEGATIVE_PROMPT)


class DalleImageGenerator:
    """Image generator using OpenAI DALL-E 3 API."""

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, prompt: str, negative_prompt: str = "") -> str | None:
        """Call OpenAI Images API and return the generated image URL."""
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-2",
                        "prompt": prompt,
                        "n": 1,
                        "size": "512x512",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                elapsed = time.monotonic() - start
                url = data["data"][0]["url"]
                logger.info("DALL-E image generated in %.2fs: %s", elapsed, url[:80])
                return url
        except Exception:
            elapsed = time.monotonic() - start
            logger.warning("DALL-E image generation failed after %.2fs", elapsed, exc_info=True)
            return None
