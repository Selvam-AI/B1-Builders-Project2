import asyncio
import os

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
from src.backend.app.services.seed import seed_database


def reset_seeded_db() -> None:
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


async def admin_headers() -> dict[str, str]:
    response = await request(
        "POST",
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def reserve_and_get_video_session(headers: dict[str, str]) -> int:
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

    sessions_response = await request("GET", "/api/video-sessions", headers=headers)
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert len(sessions) == 1
    return sessions[0]["id"]


def test_member_can_create_and_update_feedback_for_reserved_video() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("feedback1@example.com"))
    video_session_id = asyncio.run(reserve_and_get_video_session(headers))

    like_response = asyncio.run(
        request(
            "POST",
            "/api/feedback",
            headers=headers,
            json={"video_session_id": video_session_id, "value": "like"},
        )
    )
    dislike_response = asyncio.run(
        request(
            "POST",
            "/api/feedback",
            headers=headers,
            json={"video_session_id": video_session_id, "value": "dislike"},
        )
    )

    assert like_response.status_code == 200
    assert dislike_response.status_code == 200
    assert like_response.json()["id"] == dislike_response.json()["id"]
    assert dislike_response.json()["value"] == "dislike"


def test_feedback_requires_matching_reservation() -> None:
    reset_seeded_db()
    reserved_headers = asyncio.run(register_member("reserved@example.com"))
    other_headers = asyncio.run(register_member("not-reserved@example.com"))
    video_session_id = asyncio.run(reserve_and_get_video_session(reserved_headers))

    response = asyncio.run(
        request(
            "POST",
            "/api/feedback",
            headers=other_headers,
            json={"video_session_id": video_session_id, "value": "like"},
        )
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Feedback requires a matching reservation."


def test_feedback_accepts_only_like_or_dislike() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("feedback-values@example.com"))
    video_session_id = asyncio.run(reserve_and_get_video_session(headers))

    response = asyncio.run(
        request(
            "POST",
            "/api/feedback",
            headers=headers,
            json={"video_session_id": video_session_id, "value": "maybe"},
        )
    )

    assert response.status_code == 422


def test_admin_can_view_feedback_summary() -> None:
    reset_seeded_db()
    first_headers = asyncio.run(register_member("summary-like@example.com"))
    second_headers = asyncio.run(register_member("summary-dislike@example.com"))
    video_session_id = asyncio.run(reserve_and_get_video_session(first_headers))
    second_reserve_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=second_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    assert second_reserve_response.status_code == 201
    asyncio.run(
        request(
            "POST",
            "/api/feedback",
            headers=first_headers,
            json={"video_session_id": video_session_id, "value": "like"},
        )
    )
    asyncio.run(
        request(
            "POST",
            "/api/feedback",
            headers=second_headers,
            json={"video_session_id": video_session_id, "value": "dislike"},
        )
    )
    headers = asyncio.run(admin_headers())

    response = asyncio.run(request("GET", "/api/admin/feedback-summary", headers=headers))

    assert response.status_code == 200
    summary = response.json()
    assert len(summary) == 1
    assert summary[0]["video_session_id"] == video_session_id
    assert summary[0]["likes"] == 1
    assert summary[0]["dislikes"] == 1
    assert summary[0]["total_feedback"] == 2
    assert summary[0]["score"] == 0


def test_guest_cannot_submit_feedback() -> None:
    reset_seeded_db()

    response = asyncio.run(
        request("POST", "/api/feedback", json={"video_session_id": 1, "value": "like"})
    )

    assert response.status_code == 401


def test_member_cannot_view_feedback_summary() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("feedback-not-admin@example.com"))

    response = asyncio.run(request("GET", "/api/admin/feedback-summary", headers=headers))

    assert response.status_code == 403
