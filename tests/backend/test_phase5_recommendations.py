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
from src.backend.app.core.config import settings
from src.backend.app.main import app
from src.backend.app.models import VideoCacheEntry, VideoSession
from src.backend.app.services import recommendations
from src.backend.app.services.recommendations import RecommendationCandidate
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


async def login_admin() -> dict[str, str]:
    response = await request(
        "POST",
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def count_video_sessions() -> int:
    with SessionLocal() as db:
        return len(db.query(VideoSession).all())


def count_video_cache_entries() -> int:
    with SessionLocal() as db:
        return len(db.query(VideoCacheEntry).all())


def test_recommendation_endpoint_creates_mock_approved_session() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("recommend1@example.com"))

    response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["time_slot_id"] == 1
    assert payload["workout_category_id"] == 1
    assert payload["provider"] == "mock"
    assert payload["status"] == "approved"
    assert payload["duration_seconds"] == 600


def test_recommendation_is_cached_by_slot_and_category() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("recommend2@example.com"))
    payload = {"time_slot_id": 1, "workout_category_id": 1}

    first_response = asyncio.run(
        request("POST", "/api/video-sessions/recommend", headers=headers, json=payload)
    )
    second_response = asyncio.run(
        request("POST", "/api/video-sessions/recommend", headers=headers, json=payload)
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    assert count_video_sessions() == 1


def test_reservation_does_not_create_video_session_before_broadcast_window() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("recommend3@example.com"))

    reserve_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=headers,
            json={"time_slot_id": 2, "workout_category_id": 2},
        )
    )
    video_sessions_response = asyncio.run(
        request("GET", "/api/video-sessions", headers=headers)
    )

    assert reserve_response.status_code == 201
    assert video_sessions_response.status_code == 200
    sessions = video_sessions_response.json()
    assert sessions == []


def test_guest_cannot_request_recommendation() -> None:
    reset_seeded_db()

    response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )

    assert response.status_code == 401


def test_cached_embeddable_video_is_used_when_fresh_search_is_unavailable() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("recommend-cache@example.com"))
    with SessionLocal() as db:
        db.add(
            VideoSession(
                time_slot_id=1,
                workout_category_id=1,
                title="Known Embeddable Workout",
                youtube_video_id="known123",
                youtube_url="https://www.youtube.com/watch?v=known123",
                duration_seconds=600,
                provider="youtube",
                status="approved",
                safety_notes="Previously approved embeddable video.",
                agent_summary="Cached approved recommendation.",
            )
        )
        db.commit()

    response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            headers=headers,
            json={"time_slot_id": 2, "workout_category_id": 1},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "youtube-cached"
    assert payload["youtube_video_id"] == "known123"


def test_fresh_youtube_search_is_attempted_before_cached_fallback(monkeypatch) -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("recommend-fresh@example.com"))
    original_key = settings.youtube_api_key
    settings.youtube_api_key = "test-key"
    calls = {"youtube": 0}

    def fake_youtube_recommendation(_category, _excluded_video_ids=None):
        calls["youtube"] += 1
        return None

    monkeypatch.setattr(recommendations, "youtube_recommendation", fake_youtube_recommendation)
    with SessionLocal() as db:
        db.add(
            VideoSession(
                time_slot_id=1,
                workout_category_id=1,
                title="Known Embeddable Workout",
                youtube_video_id="known123",
                youtube_url="https://www.youtube.com/watch?v=known123",
                duration_seconds=600,
                provider="youtube",
                status="approved",
                safety_notes="Previously approved embeddable video.",
                agent_summary="Cached approved recommendation.",
            )
        )
        db.commit()

    try:
        response = asyncio.run(
            request(
                "POST",
                "/api/video-sessions/recommend",
                headers=headers,
                json={"time_slot_id": 2, "workout_category_id": 1},
            )
        )
    finally:
        settings.youtube_api_key = original_key

    assert response.status_code == 200
    assert calls["youtube"] == 1
    assert response.json()["provider"] == "youtube-cached"


def test_playback_failure_replaces_video_and_confirmation_marks_cacheable(monkeypatch) -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("playback-check@example.com"))
    reserve_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    assert reserve_response.status_code == 201
    recommend_response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    assert recommend_response.status_code == 200
    sessions_response = asyncio.run(request("GET", "/api/video-sessions", headers=headers))
    video_session_id = sessions_response.json()[0]["id"]

    def fake_candidate(_db, _category, excluded_video_ids=None):
        assert "HRvFxrFGqA4" in (excluded_video_ids or set())
        return RecommendationCandidate(
            title="Replacement Workout",
            youtube_video_id="replacement123",
            youtube_url="https://www.youtube.com/watch?v=replacement123",
            duration_seconds=600,
            provider="youtube",
            safety_notes="Replacement was filtered for embeddable playback.",
            agent_summary="Selected after frontend playback failure.",
        )

    monkeypatch.setattr(recommendations, "select_recommendation_candidate", fake_candidate)

    replace_response = asyncio.run(
        request(
            "POST",
            f"/api/video-sessions/{video_session_id}/replace",
            headers=headers,
            json={"failed_video_id": "HRvFxrFGqA4", "reason": "YouTube player error 150"},
        )
    )

    assert replace_response.status_code == 200
    replacement = replace_response.json()
    assert replacement["youtube_video_id"] == "replacement123"
    assert replacement["provider"] == "youtube-pending"

    playable_response = asyncio.run(
        request(
            "POST",
            f"/api/video-sessions/{video_session_id}/playable",
            headers=headers,
            json={"youtube_video_id": "replacement123"},
        )
    )

    assert playable_response.status_code == 200
    assert playable_response.json()["provider"] == "youtube"
    assert count_video_cache_entries() == 1


def test_confirmed_video_cache_serves_least_played_candidate() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("cache-select@example.com"))
    with SessionLocal() as db:
        db.add_all(
            [
                VideoCacheEntry(
                    workout_category_id=1,
                    title="Often Played",
                    youtube_video_id="played3",
                    youtube_url="https://www.youtube.com/watch?v=played3",
                    duration_seconds=600,
                    provider="youtube",
                    status="confirmed_playable",
                    play_count=2,
                    safety_notes="Confirmed playable.",
                    curator_summary="Higher play count.",
                ),
                VideoCacheEntry(
                    workout_category_id=1,
                    title="Least Played",
                    youtube_video_id="played0",
                    youtube_url="https://www.youtube.com/watch?v=played0",
                    duration_seconds=600,
                    provider="youtube",
                    status="confirmed_playable",
                    play_count=0,
                    safety_notes="Confirmed playable.",
                    curator_summary="Lowest play count.",
                ),
            ]
        )
        db.commit()

    response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "video-cache"
    assert payload["youtube_video_id"] == "played0"


def test_broadcast_start_increments_cache_play_count_and_marks_replacement_needed() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("cache-play@example.com"))
    with SessionLocal() as db:
        db.add(
            VideoCacheEntry(
                workout_category_id=1,
                title="Nearly Retired",
                youtube_video_id="retireme",
                youtube_url="https://www.youtube.com/watch?v=retireme",
                duration_seconds=600,
                provider="youtube",
                status="confirmed_playable",
                play_count=2,
                safety_notes="Confirmed playable.",
                curator_summary="One play away from replacement.",
            )
        )
        db.commit()

    reserve_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    recommend_response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    assert recommend_response.status_code == 200
    video_session_id = asyncio.run(request("GET", "/api/video-sessions", headers=headers)).json()[0]["id"]
    start_response = asyncio.run(
        request(
            "POST",
            "/api/broadcast-sessions/start",
            headers=headers,
            json={"video_session_id": video_session_id},
        )
    )

    with SessionLocal() as db:
        cache_entry = db.query(VideoCacheEntry).filter_by(youtube_video_id="retireme").one()
        assert cache_entry.play_count == 3
        assert cache_entry.status == "needs_replacement"

    assert reserve_response.status_code == 201
    assert start_response.status_code == 200


def test_admin_can_view_video_cache_and_run_curator() -> None:
    reset_seeded_db()
    admin_headers = asyncio.run(login_admin())
    with SessionLocal() as db:
        db.add(
            VideoCacheEntry(
                workout_category_id=1,
                title="Cached Admin View",
                youtube_video_id="admincache",
                youtube_url="https://www.youtube.com/watch?v=admincache",
                duration_seconds=600,
                provider="youtube",
                status="confirmed_playable",
                play_count=1,
                safety_notes="Confirmed playable.",
                curator_summary="Visible to admins.",
            )
        )
        db.commit()

    cache_response = asyncio.run(
        request("GET", "/api/admin/video-cache", headers=admin_headers)
    )
    curate_response = asyncio.run(
        request("POST", "/api/admin/video-cache/curate", headers=admin_headers)
    )

    assert cache_response.status_code == 200
    assert cache_response.json()[0]["youtube_video_id"] == "admincache"
    assert curate_response.status_code == 200
    assert curate_response.json()["categories"] == 3


def test_cardio_category_can_receive_mock_recommendation() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("recommend-cardio@example.com"))

    response = asyncio.run(
        request(
            "POST",
            "/api/video-sessions/recommend",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 3},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workout_category_id"] == 3
    assert payload["provider"] == "mock"
    assert payload["youtube_video_id"] == "VWj8ZxCxrYk"
