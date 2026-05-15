from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.backend.app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from src.backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema_updates()


def ensure_sqlite_schema_updates() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "time_slots" not in table_names:
        return

    time_slot_columns = {column["name"] for column in inspector.get_columns("time_slots")}
    with engine.begin() as connection:
        if "is_demo" not in time_slot_columns:
            connection.execute(
                text("ALTER TABLE time_slots ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT 0")
            )
