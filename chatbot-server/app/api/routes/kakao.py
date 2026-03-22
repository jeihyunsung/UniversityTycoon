import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_game_engine, get_repository
from app.models.schemas import GameResult, KakaoWebhookRequest
from app.repositories.base import SaveRepository
from app.services.callback import schedule_callback
from app.services.game_engine import GameEngine
from app.services.kakao_adapter import to_kakao_response

logger = logging.getLogger(__name__)

router = APIRouter()

CALLBACK_RESPONSE = {"version": "2.0", "useCallback": True}


def _respond(
    result: GameResult,
    request: KakaoWebhookRequest,
    game_engine: GameEngine,
) -> dict:
    """Return immediate response or trigger callback for image generation."""
    callback_url = request.user_request.callback_url
    if result.image_prompt and callback_url:
        schedule_callback(callback_url, result, game_engine._image_gen)
        return CALLBACK_RESPONSE
    return to_kakao_response(result)


@router.post("/start-game")
async def start_game(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.start_game(request, repo)
    return _respond(result, request, game_engine)


@router.post("/status")
async def status(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.load_status(request, repo)
    return to_kakao_response(result)


@router.post("/advance-turn")
async def advance_turn(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.advance_turn(request, repo)
    return to_kakao_response(result)


@router.post("/build-menu")
async def build_menu(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.build_menu(request, repo)
    return to_kakao_response(result)


@router.post("/build")
async def build(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.build(request, repo)
    return _respond(result, request, game_engine)


@router.post("/department-menu")
async def department_menu(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.department_menu(request, repo)
    return to_kakao_response(result)


@router.post("/department")
async def department(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.department(request, repo)
    return _respond(result, request, game_engine)


@router.post("/admission-menu")
async def admission_menu(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.admission_menu(request, repo)
    return to_kakao_response(result)


@router.post("/admission")
async def admission(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.admission(request, repo)
    return to_kakao_response(result)


@router.post("/logs")
async def logs(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.logs(request, repo)
    return to_kakao_response(result)


@router.post("/event-choice")
async def event_choice(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.event_choice(request, repo)
    return to_kakao_response(result)


@router.post("/quests")
async def quests(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
    game_engine: GameEngine = Depends(get_game_engine),
) -> dict:
    result = await game_engine.quests(request, repo)
    return to_kakao_response(result)
