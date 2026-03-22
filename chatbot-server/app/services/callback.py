"""Kakao callback service for async image generation."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.models.schemas import GameResult
from app.services.image_service import ImageGenerator
from app.services.kakao_adapter import to_kakao_response

logger = logging.getLogger(__name__)


async def send_callback(
    callback_url: str,
    result: GameResult,
    image_gen: ImageGenerator,
) -> None:
    """Generate image and send full response via Kakao callback URL.

    Args:
        callback_url: Kakao-provided single-use callback URL.
        result: Game result containing image prompt info.
        image_gen: Image generator instance.
    """
    try:
        image_url = await image_gen.generate(
            result.image_prompt or "",
            result.image_negative_prompt or "",
        )
        result.image_url = image_url
        payload = to_kakao_response(result)

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(callback_url, json=payload)
            logger.info(
                "Callback sent to %s — status %s", callback_url[:60], resp.status_code
            )
    except Exception:
        logger.warning("Callback failed for %s", callback_url[:60], exc_info=True)


def schedule_callback(
    callback_url: str,
    result: GameResult,
    image_gen: ImageGenerator,
) -> None:
    """Fire-and-forget: schedule callback as a background task."""
    asyncio.create_task(send_callback(callback_url, result, image_gen))
