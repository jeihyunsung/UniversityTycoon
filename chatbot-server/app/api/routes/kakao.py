from fastapi import APIRouter

from app.models.schemas import KakaoWebhookRequest
from app.services.game_engine import game_engine
from app.services.kakao_adapter import to_kakao_response


router = APIRouter()


@router.post("/start-game")
def start_game(request: KakaoWebhookRequest) -> dict:
    result = game_engine.start_game(request)
    return to_kakao_response(result)


@router.post("/status")
def status(request: KakaoWebhookRequest) -> dict:
    result = game_engine.load_status(request)
    return to_kakao_response(result)


@router.post("/advance-turn")
def advance_turn(request: KakaoWebhookRequest) -> dict:
    result = game_engine.advance_turn(request)
    return to_kakao_response(result)


@router.post("/build-menu")
def build_menu(request: KakaoWebhookRequest) -> dict:
    result = game_engine.build_menu(request)
    return to_kakao_response(result)


@router.post("/build")
def build(request: KakaoWebhookRequest) -> dict:
    result = game_engine.build(request)
    return to_kakao_response(result)


@router.post("/department-menu")
def department_menu(request: KakaoWebhookRequest) -> dict:
    result = game_engine.department_menu(request)
    return to_kakao_response(result)


@router.post("/department")
def department(request: KakaoWebhookRequest) -> dict:
    result = game_engine.department(request)
    return to_kakao_response(result)


@router.post("/admission-menu")
def admission_menu(request: KakaoWebhookRequest) -> dict:
    result = game_engine.admission_menu(request)
    return to_kakao_response(result)


@router.post("/admission")
def admission(request: KakaoWebhookRequest) -> dict:
    result = game_engine.admission(request)
    return to_kakao_response(result)


@router.post("/logs")
def logs(request: KakaoWebhookRequest) -> dict:
    result = game_engine.logs(request)
    return to_kakao_response(result)
