import os
import asyncio

os.environ["DATABASE_URL"] = "sqlite:////tmp/fithub_ai_backend_tests.db"
os.environ["AI_LLM_PROVIDER"] = "ollama"
os.environ["AI_RECOMMENDER_MODE"] = "llm"
os.environ["AI_ALLOW_MOCK_FALLBACK"] = "true"
os.environ["MODEL"] = "ollama/llama3"
os.environ["BASE_URL"] = "http://localhost:11434"
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


async def get_admin_headers(client: httpx.AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def get_json(path: str, requires_auth: bool = False):
    reset_seeded_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await get_admin_headers(client) if requires_auth else {}
        response = await client.get(path, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_status_reports_current_backend_phase() -> None:
    payload = asyncio.run(get_json("/api/status"))

    assert payload["status"] == "ok"
    assert payload["phase"] == "phase-8-video-curator"
    assert payload["ai_llm_provider"] == "ollama"
    assert payload["mock_fallback_enabled"] is True


def test_seeded_time_slots_are_hourly_from_9am_to_9pm() -> None:
    slots = asyncio.run(get_json("/api/time-slots", requires_auth=True))
    regular_slots = [slot for slot in slots if not slot["is_demo"]]

    assert len(slots) == 13
    assert slots[0]["label"] == "Demo time slot"
    assert slots[0]["is_demo"] is True
    assert len(regular_slots) == 12
    assert regular_slots[0]["label"] == "9:00 AM - 10:00 AM"
    assert regular_slots[-1]["label"] == "8:00 PM - 9:00 PM"
    assert all(slot["capacity"] == 20 for slot in regular_slots)
    assert all(slot["current_occupancy"] == 0 for slot in slots)


def test_seeded_workout_categories_match_project_scope() -> None:
    categories = asyncio.run(get_json("/api/workout-categories", requires_auth=True))

    assert [category["slug"] for category in categories] == [
        "upper-body",
        "lower-body",
        "cardio",
    ]


def test_video_sessions_start_empty() -> None:
    video_sessions = asyncio.run(get_json("/api/video-sessions", requires_auth=True))

    assert video_sessions == []
