"""API-level integration tests for the Kakao webhook endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.repositories.in_memory import save_repository


def _payload(user_key: str) -> dict:
    return {
        "userRequest": {
            "user": {"id": user_key, "type": "botUserKey", "properties": {}},
            "utterance": "",
            "block": {},
            "params": {},
        },
        "action": {"name": "ACTION_STATUS", "params": {}},
        "bot": {},
        "intent": {},
    }


def _action_payload(user_key: str, action_name: str) -> dict:
    payload = _payload(user_key)
    payload["action"] = {"name": action_name, "params": {}}
    return payload


@pytest.fixture
async def client():
    """Async HTTP client targeting the ASGI app directly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def clear_in_memory_repo():
    """Wipe the singleton in-memory repository before each test for isolation."""
    save_repository._saves.clear()
    yield
    save_repository._saves.clear()


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_start_game_returns_kakao_format(client: AsyncClient) -> None:
    user_key = "integration_test_user_start"
    resp = await client.post("/webhooks/kakao/start-game", json=_payload(user_key))
    assert resp.status_code == 200

    body = resp.json()
    assert body["version"] == "2.0"
    assert "template" in body
    assert "outputs" in body["template"]
    assert "quickReplies" in body["template"]


async def test_full_game_loop(client: AsyncClient) -> None:
    user_key = "integration_test_user_loop"

    # Start game
    resp = await client.post("/webhooks/kakao/start-game", json=_payload(user_key))
    assert resp.status_code == 200

    # Check status
    resp = await client.post("/webhooks/kakao/status", json=_payload(user_key))
    assert resp.status_code == 200
    text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
    assert "예산 480G" in text

    # Advance turn
    resp = await client.post("/webhooks/kakao/advance-turn", json=_payload(user_key))
    assert resp.status_code == 200

    # Build classroom
    resp = await client.post(
        "/webhooks/kakao/build",
        json=_action_payload(user_key, "ACTION_BUILD_CLASSROOM"),
    )
    assert resp.status_code == 200

    # Open computer science department
    resp = await client.post(
        "/webhooks/kakao/department",
        json=_action_payload(user_key, "ACTION_DEPT_COMPUTER"),
    )
    assert resp.status_code == 200

    # Change admission policy to hard
    resp = await client.post(
        "/webhooks/kakao/admission",
        json=_action_payload(user_key, "ACTION_ADMISSION_HARD"),
    )
    assert resp.status_code == 200


async def test_kakao_response_has_quick_replies(client: AsyncClient) -> None:
    user_key = "integration_test_user_qr"

    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))

    resp = await client.post("/webhooks/kakao/status", json=_payload(user_key))
    assert resp.status_code == 200

    qrs = resp.json()["template"]["quickReplies"]
    assert len(qrs) > 0
    assert all("label" in qr for qr in qrs)


async def test_event_choice_endpoint_no_pending(client):
    user_key = "event_test_no_pending"
    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))

    payload = _payload(user_key)
    payload["action"] = {"name": "EVENT_CHOICE", "params": {"choice": "a"}}
    resp = await client.post("/webhooks/kakao/event-choice", json=payload)
    assert resp.status_code == 200
    text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
    assert "진행 중인 이벤트가 없습니다" in text


async def test_event_choice_endpoint_success(client):
    user_key = "event_test_success"
    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))

    # Manually set pending_event
    from app.repositories.in_memory import save_repository
    save = await save_repository.get(user_key)
    save.pending_event = "big_donation"
    await save_repository.put(user_key, save)

    payload = _payload(user_key)
    payload["action"] = {"name": "EVENT_CHOICE", "params": {"choice": "a"}}
    resp = await client.post("/webhooks/kakao/event-choice", json=payload)
    assert resp.status_code == 200
    text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
    assert "선택했습니다" in text


async def test_quests_endpoint(client):
    user_key = "quest_test_user"
    await client.post("/webhooks/kakao/start-game", json=_payload(user_key))
    resp = await client.post("/webhooks/kakao/quests", json=_payload(user_key))
    assert resp.status_code == 200
    text = resp.json()["template"]["outputs"][0]["simpleText"]["text"]
    assert "마일스톤" in text or "신생 대학" in text
