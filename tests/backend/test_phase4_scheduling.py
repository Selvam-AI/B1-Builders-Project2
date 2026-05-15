import asyncio
import os

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
from src.backend.app.models import TimeSlot
from src.backend.app.services.seed import seed_database


def reset_seeded_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)


def set_slot_capacity(time_slot_id: int, capacity: int) -> None:
    with SessionLocal() as db:
        slot = db.get(TimeSlot, time_slot_id)
        assert slot is not None
        slot.capacity = capacity
        db.commit()


async def request(method: str, path: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


async def register_member(email: str) -> dict[str, str]:
    response = await request(
        "POST",
        "/api/auth/register",
        json={
            "name": email.split("@")[0],
            "email": email,
            "password": "member123",
        },
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


def test_member_can_reserve_and_cancel_slot() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("scheduler1@example.com"))

    reserve_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )

    assert reserve_response.status_code == 201
    reservation = reserve_response.json()
    assert reservation["time_slot_id"] == 1
    assert reservation["workout_category_id"] == 1

    mine_response = asyncio.run(request("GET", "/api/reservations/me", headers=headers))

    assert mine_response.status_code == 200
    assert [item["id"] for item in mine_response.json()] == [reservation["id"]]

    cancel_response = asyncio.run(
        request("DELETE", f"/api/reservations/{reservation['id']}", headers=headers)
    )

    assert cancel_response.status_code == 204
    after_cancel_response = asyncio.run(request("GET", "/api/reservations/me", headers=headers))
    assert after_cancel_response.json() == []


def test_member_cannot_duplicate_same_slot_reservation() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("scheduler2@example.com"))
    payload = {"time_slot_id": 1, "workout_category_id": 1}

    first_response = asyncio.run(
        request("POST", "/api/reservations", headers=headers, json=payload)
    )
    duplicate_response = asyncio.run(
        request("POST", "/api/reservations", headers=headers, json=payload)
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Member already reserved this time slot."


def test_member_can_change_category_for_existing_slot_reservation() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("scheduler-category@example.com"))

    first_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    update_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=headers,
            json={"time_slot_id": 1, "workout_category_id": 2},
        )
    )
    mine_response = asyncio.run(request("GET", "/api/reservations/me", headers=headers))

    assert first_response.status_code == 201
    assert update_response.status_code == 201
    assert update_response.json()["id"] == first_response.json()["id"]
    assert update_response.json()["workout_category_id"] == 2
    assert len(mine_response.json()) == 1
    assert mine_response.json()[0]["workout_category_id"] == 2


def test_slot_capacity_is_enforced() -> None:
    reset_seeded_db()
    set_slot_capacity(time_slot_id=1, capacity=1)
    first_headers = asyncio.run(register_member("capacity1@example.com"))
    second_headers = asyncio.run(register_member("capacity2@example.com"))

    first_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=first_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    full_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=second_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )

    assert first_response.status_code == 201
    assert full_response.status_code == 409
    assert full_response.json()["detail"] == "Time slot is full."


def test_admin_can_view_occupancy_summary() -> None:
    reset_seeded_db()
    member_headers = asyncio.run(register_member("occupancy@example.com"))
    asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=member_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    headers = asyncio.run(admin_headers())

    response = asyncio.run(request("GET", "/api/admin/occupancy", headers=headers))

    assert response.status_code == 200
    occupancy = response.json()
    regular_occupancy = [slot for slot in occupancy if not slot["is_demo"]]
    assert len(occupancy) == 13
    assert len(regular_occupancy) == 12
    assert regular_occupancy[0]["current_occupancy"] == 1
    assert regular_occupancy[0]["remaining_capacity"] == 19
    assert regular_occupancy[0]["is_full"] is False


def test_member_cannot_view_admin_occupancy() -> None:
    reset_seeded_db()
    headers = asyncio.run(register_member("not-admin@example.com"))

    response = asyncio.run(request("GET", "/api/admin/occupancy", headers=headers))

    assert response.status_code == 403
