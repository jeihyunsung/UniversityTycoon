from fastapi import APIRouter, Depends

from app.api.deps import get_repository
from app.models.schemas import KakaoWebhookRequest
from app.repositories.base import SaveRepository
from app.services.game_engine import game_engine
from app.services.kakao_adapter import to_kakao_response


router = APIRouter()


@router.post("/start-game")
async def start_game(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.start_game(request, repo)
    return to_kakao_response(result)


@router.post("/status")
async def status(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.load_status(request, repo)
    return to_kakao_response(result)


@router.post("/advance-turn")
async def advance_turn(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.advance_turn(request, repo)
    return to_kakao_response(result)


@router.post("/build-menu")
async def build_menu(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.build_menu(request, repo)
    return to_kakao_response(result)


@router.post("/build")
async def build(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.build(request, repo)
    return to_kakao_response(result)


@router.post("/department-menu")
async def department_menu(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.department_menu(request, repo)
    return to_kakao_response(result)


@router.post("/department")
async def department(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.department(request, repo)
    return to_kakao_response(result)


@router.post("/admission-menu")
async def admission_menu(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.admission_menu(request, repo)
    return to_kakao_response(result)


@router.post("/admission")
async def admission(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.admission(request, repo)
    return to_kakao_response(result)


@router.post("/logs")
async def logs(
    request: KakaoWebhookRequest,
    repo: SaveRepository = Depends(get_repository),
) -> dict:
    result = await game_engine.logs(request, repo)
    return to_kakao_response(result)
