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


def test_member_can_register_with_email_and_receive_token() -> None:
    reset_seeded_db()

    response = asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Email Member",
                "age": 24,
                "email": "email-member@example.com",
                "password": "member123",
                "preferred_time_slots": [9, 18],
            },
        )
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["role"] == "member"
    assert payload["access_token"]


def test_member_registration_requires_email() -> None:
    reset_seeded_db()

    response = asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Missing Email",
                "age": 28,
                "password": "member123",
            },
        )
    )

    assert response.status_code == 422


def test_member_registration_validates_email() -> None:
    reset_seeded_db()

    response = asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Bad Email",
                "age": 28,
                "email": "not-an-email",
                "password": "member123",
            },
        )
    )

    assert response.status_code == 422


def test_member_login_and_me_endpoint() -> None:
    reset_seeded_db()

    asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Member One",
                "age": 31,
                "email": "member1@example.com",
                "password": "member123",
                "preferred_time_slots": [10],
            },
        )
    )
    login_response = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "member1@example.com", "password": "member123"},
        )
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    me_response = asyncio.run(
        request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    )

    assert me_response.status_code == 200
    user = me_response.json()
    assert user["email"] == "member1@example.com"
    assert user["role"] == "member"
    assert user["preferred_time_slots"] == [10]


def test_seeded_admin_can_access_admin_summary() -> None:
    reset_seeded_db()

    login_response = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    summary_response = asyncio.run(
        request("GET", "/api/admin/summary", headers={"Authorization": f"Bearer {token}"})
    )

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["admin"] == "admin@example.com"
    assert summary["time_slots"] == 13


def test_admin_can_list_and_pause_member_accounts() -> None:
    reset_seeded_db()

    member_response = asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Managed Member",
                "email": "managed-member@example.com",
                "password": "member123",
            },
        )
    )
    admin_login = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    users_response = asyncio.run(request("GET", "/api/admin/users", headers=admin_headers))
    assert users_response.status_code == 200
    member_id = users_response.json()[0]["id"]
    pause_response = asyncio.run(
        request(
            "PATCH",
            f"/api/admin/users/{member_id}/status",
            headers=admin_headers,
            json={"is_active": False},
        )
    )
    login_after_pause = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "managed-member@example.com", "password": "member123"},
        )
    )

    assert users_response.json()[0]["email"] == "managed-member@example.com"
    assert pause_response.status_code == 200
    assert pause_response.json()["is_active"] is False
    assert login_after_pause.status_code == 403


def test_admin_can_delete_member_account() -> None:
    reset_seeded_db()

    member_response = asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Deleted Member",
                "email": "deleted-member@example.com",
                "password": "member123",
            },
        )
    )
    member_headers = {"Authorization": f"Bearer {member_response.json()['access_token']}"}
    reserve_response = asyncio.run(
        request(
            "POST",
            "/api/reservations",
            headers=member_headers,
            json={"time_slot_id": 1, "workout_category_id": 1},
        )
    )
    admin_login = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    member_id = member_response.json()["user"]["id"] if "user" in member_response.json() else None
    users_response = asyncio.run(request("GET", "/api/admin/users", headers=admin_headers))
    member_id = member_id or users_response.json()[0]["id"]

    delete_response = asyncio.run(
        request("DELETE", f"/api/admin/users/{member_id}", headers=admin_headers)
    )
    users_after_delete = asyncio.run(request("GET", "/api/admin/users", headers=admin_headers))
    login_after_delete = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "deleted-member@example.com", "password": "member123"},
        )
    )

    assert reserve_response.status_code == 201
    assert delete_response.status_code == 204
    assert users_after_delete.status_code == 200
    assert users_after_delete.json() == []
    assert login_after_delete.status_code == 401


def test_admin_account_cannot_be_deleted_through_member_management() -> None:
    reset_seeded_db()

    admin_login = asyncio.run(
        request(
            "POST",
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    me_response = asyncio.run(request("GET", "/api/auth/me", headers=admin_headers))

    delete_response = asyncio.run(
        request("DELETE", f"/api/admin/users/{me_response.json()['id']}", headers=admin_headers)
    )

    assert delete_response.status_code == 404


def test_member_cannot_access_admin_summary() -> None:
    reset_seeded_db()

    register_response = asyncio.run(
        request(
            "POST",
            "/api/auth/register",
            json={
                "name": "Member Two",
                "email": "member2@example.com",
                "password": "member123",
            },
        )
    )
    token = register_response.json()["access_token"]
    summary_response = asyncio.run(
        request("GET", "/api/admin/summary", headers={"Authorization": f"Bearer {token}"})
    )

    assert summary_response.status_code == 403


def test_guest_cannot_access_dashboard_data() -> None:
    reset_seeded_db()

    response = asyncio.run(request("GET", "/api/video-sessions"))

    assert response.status_code == 401
