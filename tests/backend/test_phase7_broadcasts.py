import asyncio
import os
import time

os.environ["DATABASE_URL"] = "sqlite:////tmp/fithub_ai_backend_tests.db"
os.environ["AI_LLM_PROVIDER"] = "ollama"
os.environ["AI_RECOMMENDER_MODE"] = "llm"
os.environ["AI_ALLOW_MOCK_FALLBACK"] = "true"
os.environ["MODEL"] = "ollama/llama3"
os.environ["BASE_URL"] = "http://localhost:11434"
os.environ["YOUTUBE_API_KEY"] = ""
os.environ["SEED_ADMIN"] = "true"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["SECRET_KEY"] = "test-secret"

import httpx

from src.backend.app.core.database import Base, SessionLocal, engine
from src.backend.app.main import app
from src.backend.app.services.broadcasts import clear_broadcast_sessions
from src.backend.app.services.seed import seed_database


def reset_seeded_db() -> None:
    clear_broadcast_sessions()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)


async def request(method: str, path: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


async def register_member(email: str) -> dict[str, str]:
    response = await request(
        "POST",
        "/api/auth/register",
        json={"name": email.split("@")[0], "email": email, "password": "member123"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def reserve_and_recommend(headers: dict[str, str]) -> int:
    reserve_response = await request(
        "POST",
        "/api/reservations",
        headers=headers,
        json={"time_slot_id": 1, "workout_category_id": 1},
    )
    assert reserve_response.status_code == 201
    recommend_response = await request(
        "POST",
        "/api/video-sessions/recommend",
        headers=headers,
        json={"time_slot_id": 1, "workout_category_id": 1},
    )
    assert recommend_response.status_code == 200
    return int(recommend_response.json()["id"])


def test_broadcast_start_returns_shared_playback_offset_for_late_joiner() -> None:
    reset_seeded_db()
    first_headers = asyncio.run(register_member("broadcast1@example.com"))
    second_headers = asyncio.run(register_member("broadcast2@example.com"))
    video_session_id = asyncio.run(reserve_and_recommend(first_headers))
    second_reserve = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=second_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    assert second_reserve.status_code == 201

    first_start = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=first_headers,
            json={"video_session_id": video_session_id},
        )
    )
    time.sleep(1.1)
    second_start = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=second_headers,
            json={"video_session_id": video_session_id},
        )
    )

    assert first_start.status_code == 200
    assert second_start.status_code == 200
    first_payload = first_start.json()
    second_payload = second_start.json()
    assert first_payload["video_session_id"] == second_payload["video_session_id"]
    assert first_payload["started_at"] == second_payload["started_at"]
    assert second_payload["playback_offset_seconds"] >= 1
    assert second_payload["participant_count"] == 2


def test_user_can_start_fresh_broadcast_after_empty_session() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("broadcast-exit@example.com"))
    video_session_id = asyncio.run(reserve_and_recommend(headers))

    start_response = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=headers,
            json={"video_session_id": video_session_id},
        )
    )
    exit_response = asyncio.run(
        request("POST", f"/api/broadcast-sessions/{video_session_id}/exit", headers=headers)
    )
    rejoin_response = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=headers,
            json={"video_session_id": video_session_id},
        )
    )

    assert start_response.status_code == 200
    assert exit_response.status_code == 200
    assert exit_response.json()["participant_count"] == 0
    assert exit_response.json()["status"] == "ended"
    assert rejoin_response.status_code == 200
    assert rejoin_response.json()["participant_count"] == 1
    assert rejoin_response.json()["status"] == "active"


def test_user_cannot_rejoin_same_active_broadcast_after_exiting() -> None:
    reset_seeded_db()
    first_headers = asyncio.run(register_member("broadcast-exit-active1@example.com"))
    second_headers = asyncio.run(register_member("broadcast-exit-active2@example.com"))
    video_session_id = asyncio.run(reserve_and_recommend(first_headers))
    second_reserve = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=second_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    assert second_reserve.status_code == 201

    first_start = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=first_headers,
            json={"video_session_id": video_session_id},
        )
    )
    second_start = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=second_headers,
            json={"video_session_id": video_session_id},
        )
    )
    first_exit = asyncio.run(
        request("POST", f"/api/broadcast-sessions/{video_session_id}/exit", headers=first_headers)
    )
    first_rejoin = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=first_headers,
            json={"video_session_id": video_session_id},
        )
    )

    assert first_start.status_code == 200
    assert second_start.status_code == 200
    assert first_exit.status_code == 200
    assert first_exit.json()["participant_count"] == 1
    assert first_rejoin.status_code == 403
